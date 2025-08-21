import asyncio
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_query_sends_storechat(monkeypatch):
    # Provide a minimal fake uagents.Agent with a send method to avoid importing the real package
    class FakeAgent:
        async def send(self, dest, msg):
            return True

    import sys
    import types
    fake_uagents = types.SimpleNamespace(Agent=FakeAgent)
    monkeypatch.setitem(sys.modules, 'uagents', fake_uagents)

    import orchestrator_simple as orch

    client = TestClient(orch.app)
    resp = client.post("/query", json={"text": "berapa harga bitcoin"})
    assert resp.status_code == 200
    data = resp.json()
    assert "entry_id" in data
    assert "reply" in data


def test_health_endpoint_exposes_status(monkeypatch):
    # Provide a minimal fake uagents.Agent
    class FakeAgent:
        def __init__(self):
            self.address = "agent-x"

    import sys
    import types
    fake_uagents = types.SimpleNamespace(Agent=FakeAgent)
    monkeypatch.setitem(sys.modules, 'uagents', fake_uagents)

    import orchestrator_simple as orch
    client = TestClient(orch.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
