Pluto - Demo & Runbook

Quick start (local, minimal):

1. Backend agents

```bash
cd agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# in separate terminals:
python storage_agent.py
# and
uvicorn orchestrator_simple:app --host 127.0.0.1 --port 8001
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
# or run mock api
npm run mock
```

3. Try sample query (curl):

```bash
curl -X POST http://127.0.0.1:8001/query -H 'Content-Type: application/json' -d '{"text":"berapa harga bitcoin"}'
```

Notes
- For on-chain storage enable ICP settings in `.env` in `agents/` (CANISTER_ID, ICP_NETWORK_URL, STORAGE_AGENT_KEY_PATH)
- CI is configured in `.github/workflows/ci.yml` to run tests and build frontend
