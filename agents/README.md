StorageAgent
============

Purpose
-------
StorageAgent is a uAgent that writes chat entries to an Internet Computer canister using ic-py.

Quickstart (dry-run)
--------------------
1. Create a Python virtualenv and install dependencies:

```bash
python3 -m venv agents/venv
source agents/venv/bin/activate
pip install -r agents/requirements.txt
```

2. Run in dry-run mode (no ICP URL set):

```bash
# Ensure CANISTER_ID is set in env or .env
export CANISTER_ID=replace-with-local-canister-id
python agents/storage_agent.py
```

Local integration (requires ic-py and running dfx replica)
---------------------------------------------------------
1. Start local dfx replica and deploy canister:

```bash
dfx start --background
cd icp_canister
dfx deploy
```

2. Set env and run agent with ic-py available:

```bash
export ICP_NETWORK_URL=http://127.0.0.1:4943
export CANISTER_ID=$(dfx canister id icp_canister_backend)
# optionally: export STORAGE_AGENT_KEY_PATH=/path/to/key.pem
python agents/storage_agent.py
```

API
---
StorageAgent listens for `StoreChat` messages on the uAgent bus where `entry` is the chat text and `entry_id` optional.

Notes
-----
- Do not commit private keys. Use environment variables or a secret store.
- For hackathon demo dry-run is sufficient; for full integration provide ic-py and a valid identity.
