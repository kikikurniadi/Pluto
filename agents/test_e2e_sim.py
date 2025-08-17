import asyncio
from unittest.mock import patch, AsyncMock

import pytest

import e2e_sim
import importlib


@pytest.mark.asyncio
async def test_e2e_sim_calls_handler_and_dry_run(monkeypatch):
    # Ensure ICP_NETWORK_URL env is empty to force dry-run
    monkeypatch.setenv("ICP_NETWORK_URL", "")

    # Import storage_agent lazily (after env is set) to avoid import-time side-effects
    storage_agent = importlib.import_module("storage_agent")

    # Patch storage_agent.call_add_chat_entry_direct to avoid any network
    async def fake_call(entry_id, entry):
        return {"ok": True, "dry_run": True}

    monkeypatch.setattr(storage_agent, "call_add_chat_entry_direct", fake_call)

    # Run the e2e simulation run_once directly
    await e2e_sim.run_once("berapa harga bitcoin")
