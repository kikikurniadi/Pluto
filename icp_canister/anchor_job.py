"""
Simple Merkle root proof-of-concept.

Usage:
  python anchor_job.py data/hashes.json

`data/hashes.json` should contain a JSON array of lowercase hex-encoded 32-byte hashes (without 0x prefix).

This script prints the merkle root and can optionally call an ICP canister if `ic-py` is configured and
environment variables `ICP_REPLICA_URL` and `CANISTER_ID` are set.
"""
import sys
import json
import hashlib
import os
from pathlib import Path

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def merkle_root_from_hex(hashes: list[str]) -> str | None:
    if not hashes:
        return None
    hs = [h.lower() for h in hashes]
    # ensure even
    while len(hs) > 1:
        if len(hs) % 2 == 1:
            hs.append(hs[-1])
        next_hs = []
        for i in range(0, len(hs), 2):
            a = bytes.fromhex(hs[i])
            b = bytes.fromhex(hs[i+1])
            next_hs.append(sha256_hex(a + b))
        hs = next_hs
    return hs[0]

def main(path: str):
    p = Path(path)
    if not p.exists():
        print("No hashes file found at", path)
        return
    data = json.loads(p.read_text())
    root = merkle_root_from_hex(data)
    print("merkle_root:", root)

    # Optional: call canister via ic-py if configured
    replica = os.environ.get("ICP_REPLICA_URL") or os.environ.get("ICP_NETWORK_URL")
    canister = os.environ.get("CANISTER_ID")
    if replica and canister:
        try:
                from ic.client import Client
                from ic.identity import Identity
                from ic.agent import Agent as ICAgent
                from ic.candid import encode, Types
        except Exception as e:
            print("ic-py not available; skipping canister call", e)
            return

        client = Client(url=replica)
        identity_path = os.environ.get("STORAGE_AGENT_KEY_PATH")
        # If no identity provided, use an anonymous identity so calls become read-only where supported
        identity = None
        if identity_path and Path(identity_path).exists():
            # Identity.from_pem expects the PEM string
            with open(identity_path, "r") as f:
                identity = Identity.from_pem(f.read())
        else:
            # create an anonymous identity
            identity = Identity("", anonymous=True)

        agent = ICAgent(identity, client)
        # Candid encode: two text params (root, batch_id)
        args = encode([
            {"type": Types.Text, "value": root},
            {"type": Types.Text, "value": "batch-1"},
        ])
        print("Calling canister anchor_root on", canister)
        res = agent.update_raw(canister_id=canister, method_name="anchor_root", arg=args)
        print("canister call result:", res)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/hashes.json")
