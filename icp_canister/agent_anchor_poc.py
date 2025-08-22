"""
POC: Agent -> ICP anchor flow

This script uses the local AgentVerse POC client to generate summaries for a
list of queries, computes content hashes (sha256), signs them using the
provenance HMAC POC, appends the hex hashes to `data/hashes.json`, and then
invokes `anchor_job.py` to compute the Merkle root and optionally call the
ICP canister if `ICP_REPLICA_URL` and `CANISTER_ID` are set.

Usage:
  python agent_anchor_poc.py

Notes:
- This is a local POC and uses HMAC signatures for simplicity. Replace with
  asymmetric signatures before production use.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import hashlib
import os
import subprocess

from agents.agentverse import AgentVerseClient
from agents.provenance import sign_hex

DATA_DIR = Path(__file__).parent / "data"
HASHES_FILE = DATA_DIR / "hashes.json"

SAMPLE_QUERIES = [
    "Harga bitcoin hari ini",
    "Berita terbaru tentang ICP",
    "Analisis pasar kripto minggu ini",
]

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HASHES_FILE.exists():
        HASHES_FILE.write_text("[]")

def load_hashes() -> list[str]:
    try:
        return json.loads(HASHES_FILE.read_text())
    except Exception:
        return []

def save_hashes(hashes: list[str]):
    HASHES_FILE.write_text(json.dumps(hashes, indent=2))

def run_anchor_job():
    print("Running anchor_job.py to compute merkle root...")
    proc = subprocess.run(["python", str(Path(__file__).parent / "anchor_job.py"), str(HASHES_FILE)], capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print("anchor_job failed:", proc.stderr)

def main():
    ensure_data_dir()
    client = AgentVerseClient()
    hashes = load_hashes()
    print(f"Loaded {len(hashes)} existing hashes")

    for q in SAMPLE_QUERIES:
        res = client.query(q)
        summary = res.get("summary", q)
        content_hash = sha256_hex(summary.encode())
        sig = sign_hex(content_hash)
        entry = {"query": q, "summary": summary, "hash": content_hash, "signature": sig, "timestamp": datetime.utcnow().isoformat()+"Z"}
        print("Produced entry:", entry)
        if content_hash not in hashes:
            hashes.append(content_hash)

    save_hashes(hashes)
    print(f"Saved {len(hashes)} hashes to {HASHES_FILE}")
    run_anchor_job()

if __name__ == "__main__":
    main()
