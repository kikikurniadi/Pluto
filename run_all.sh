#!/usr/bin/env bash
set -euo pipefail

# Start storage_agent and orchestrator_simple for a local demo (foreground)
cd agents
source venv/bin/activate || true
# run storage_agent in background
python storage_agent.py &
STORAGE_PID=$!
# run orchestrator
uvicorn orchestrator_simple:app --host 127.0.0.1 --port 8001

# cleanup
kill $STORAGE_PID || true
