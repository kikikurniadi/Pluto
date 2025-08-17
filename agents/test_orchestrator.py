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
