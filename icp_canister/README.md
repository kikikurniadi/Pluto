# icp_canister

Minimal canister skeleton for Pluto POC — anchors Merkle roots on the Internet Computer (ICP).

What this folder contains:
- `src/main.mo` - Motoko canister implementing a tiny anchor registry (anchor_root, get_anchor, list_anchors).
- `candid.did` - Candid interface for the canister.
- `anchor_job.py` - simple Python proof-of-concept that computes a Merkle root from a JSON list of hex hashes and prints it (optional: calls canister via ic-py if configured).
- `dfx.json` - placeholder dfx config template (edit before local dfx deploy).

Notes
- This is a POC. Do NOT store plaintext user data on-chain — only store hashes/roots.
- To run canister locally you need the DFINITY SDK (`dfx`) and to adapt `dfx.json`.

Next steps
- Fill `dfx.json` with your canister name and IDs, implement canister build/deploy in CI, and wire `anchor_job.py` to call the canister via `ic-py` or `dfx`.
