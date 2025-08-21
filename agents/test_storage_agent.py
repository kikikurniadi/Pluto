import asyncio
from unittest.mock import patch, AsyncMock
import pytest

# We will import the module under test and patch ic-py related calls
import storage_agent as sa


@pytest.mark.asyncio
async def test_encode_args_error_when_icpy_missing():
    # encode should raise if ic-py is not available
    with patch("storage_agent.encode", None):
        with pytest.raises(RuntimeError):
            sa.encode_args_for_add("id", "entry")


@pytest.mark.asyncio
async def test_call_add_chat_entry_direct_dry_run(monkeypatch):
    cfg_canister = sa.CANISTER_ID
    # ensure ICP_NETWORK_URL is None to force dry-run
    monkeypatch.setenv("ICP_NETWORK_URL", "")
    res = await sa.call_add_chat_entry_direct("id-1", "hello")
    assert res.get("ok") is True
    assert res.get("dry_run") is True


def test_storage_health_helper():
    import storage_agent as sa
    h = sa.health()
    assert "canister" in h
    assert "icpy" in h
