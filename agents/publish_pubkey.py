#!/usr/bin/env python3
"""Publish the provenance public key PEM to the ICP canister using ic-py.

Usage: set CANISTER_ID, ICP_REPLICA_URL (or ICP_NETWORK_URL) and STORAGE_AGENT_KEY_PATH env vars, then run.
If STORAGE_AGENT_KEY_PATH is not set, the script will print the PEM and exit.
"""
import os
from pathlib import Path

KEY_PATH = os.environ.get("PROVENANCE_KEY_PATH", "provenance_key.pem")
CANISTER = os.environ.get("CANISTER_ID")
REPLICA = os.environ.get("ICP_REPLICA_URL") or os.environ.get("ICP_NETWORK_URL")
IDENTITY_PATH = os.environ.get("STORAGE_AGENT_KEY_PATH")


def main():
    p = Path(KEY_PATH)
    if not p.exists():
        print("Provenance key not found at", KEY_PATH)
        print("Generate by signing once or create a key at that location.")
        return 2
    # derive public PEM from private key to avoid publishing the private key
    pem = derive_public_pem(p)
    if not (REPLICA and CANISTER and IDENTITY_PATH):
        print("ICP not fully configured. Returning PEM and skipping on-chain publish.")
        print(pem)
        return 0

    try:
        from ic.client import Client
        from ic.identity import Identity
        from ic.agent import Agent as ICAgent
        from ic.candid import encode, Types
    except Exception as e:
        print("ic-py not available:", e)
        print("Install with: pip install ic-py")
        return 3

    client = Client(url=REPLICA)
    # load identity
    idp = Path(IDENTITY_PATH)
    if not idp.exists():
        print("STORAGE_AGENT_KEY_PATH does not exist:", IDENTITY_PATH)
        return 4
    identity = Identity.from_pem(idp.read_text())
    agent = ICAgent(identity, client)

    # build candid arg: a single text param
    try:
        arg = encode([{"type": Types.Text, "value": pem}])
    except Exception as e:
        print("Failed to encode candid arg:", e)
        return 5

    try:
        print("Calling set_pubkey on canister", CANISTER, "via", REPLICA)
        res = agent.update_raw(canister_id=CANISTER, method_name="set_pubkey", arg=arg)
        print("Published, response:", res)
        return 0
    except Exception as e:
        print("Publish failed:", e)
        return 6


if __name__ == '__main__':
    raise SystemExit(main())


def derive_public_pem(path: Path) -> str:
    """Return the public key PEM derived from private key at `path`.

    If cryptography is unavailable or derivation fails, return the raw file text.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        priv = serialization.load_pem_private_key(path.read_bytes(), password=None)
        pub = priv.public_key()
        return pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    except Exception:
        return path.read_text()
