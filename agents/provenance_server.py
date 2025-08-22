"""
Lightweight provenance HTTP server for POC.

Endpoints:
- POST /sign {"content_hash": "..."} -> { signature, timestamp }
- POST /verify {"content_hash":"...", "signature":"..."} -> { ok: true/false }
- POST /anchor -> triggers the anchor_job to compute merkle root from data/hashes.json (optional: call canister if configured)

Run locally:
  uvicorn agents.provenance_server:app --reload --port 9001

This is a POC — in production use proper auth, rate limits, and asymmetric signatures.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import subprocess
import json
from pathlib import Path
from .provenance import sign_hex, verify_hex
from pathlib import Path
import os
from typing import Optional
try:
    from ic.client import Client
    from ic.identity import BasicIdentity
    from ic.agent import Agent as ICAgent
    from ic.candid import encode
except Exception:
    Client = None
    BasicIdentity = None
    ICAgent = None
    encode = None

app = FastAPI(title="Pluto Provenance POC")


class SignRequest(BaseModel):
    content_hash: str


class VerifyRequest(BaseModel):
    content_hash: str
    signature: str


@app.post("/sign")
def sign(req: SignRequest):
    # naive validation
    if not req.content_hash or len(req.content_hash) < 64:
        raise HTTPException(status_code=400, detail="invalid content_hash")
    sig = sign_hex(req.content_hash)
    return {"signature": sig, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/verify")
def verify(req: VerifyRequest):
    ok = verify_hex(req.content_hash, req.signature)
    return {"ok": ok}


@app.post("/anchor")
def anchor():
    # Run the anchor_job to compute merkle root; return output. This is a local POC only.
    script = "icp_canister/anchor_job.py"
    if not Path(script).exists():
        raise HTTPException(status_code=500, detail=f"anchor job not found: {script}")
    try:
        proc = subprocess.run(["python", script, "data/hashes.json"], capture_output=True, text=True, check=True)
        return {"ok": True, "output": proc.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail={"err": e.stderr, "out": e.stdout})


@app.get("/pubkey")
def pubkey():
    # Return the public key PEM for clients to verify signatures
    key_path = os.environ.get("PROVENANCE_KEY_PATH", "provenance_key.pem")
    p = Path(key_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="public key not found; generate key by signing once")
    # derive public key PEM
    from cryptography.hazmat.primitives import serialization
    priv = serialization.load_pem_private_key(p.read_bytes(), password=None)
    pub = priv.public_key()
    pem = pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return {"pubkey_pem": pem}


@app.post("/publish_pubkey")
def publish_pubkey():
    # Publish the public key to the ICP canister if ic-py and ICP env are configured
    key_path = os.environ.get("PROVENANCE_KEY_PATH", "provenance_key.pem")
    p = Path(key_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="key not found")
    # derive public PEM from private key to avoid publishing private key
    try:
        from cryptography.hazmat.primitives import serialization
        priv = serialization.load_pem_private_key(p.read_bytes(), password=None)
        pub = priv.public_key()
        pem = pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    except Exception:
        pem = p.read_text()
    # if ICP not configured, return PEM only
    replica = os.environ.get("ICP_REPLICA_URL") or os.environ.get("ICP_NETWORK_URL")
    canister = os.environ.get("CANISTER_ID")
    if not replica or not canister or Client is None:
        return {"ok": True, "pubkey": pem, "published": False}

    # build client and agent
    client = Client(url=replica)
    identity_path = os.environ.get("STORAGE_AGENT_KEY_PATH")
    identity = None
    if identity_path and Path(identity_path).exists():
        with open(identity_path, "rb") as f:
            identity = BasicIdentity.from_pem(f.read())
    agent = ICAgent(identity, client)

    try:
        args = encode((pem, ), "(text)")
        res = agent.update_raw(canister_id=canister, method_name="set_pubkey", arg=args)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
