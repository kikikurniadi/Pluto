
import os
import sys
import uuid
import logging
import asyncio
from dotenv import load_dotenv
from typing import Any

# Optional imports for ic-py; we support dry-run if not installed
try:
    from ic.client import Client
    from ic.identity import BasicIdentity
    from ic.agent import Agent as ICAgent
    from ic.candid import encode
except Exception:
    Client = None
    BasicIdentity = None
    ICAgent = None
    encode = None

# Muat variabel dari file .env
load_dotenv()

logger = logging.getLogger("storage_agent")
logging.basicConfig(level=logging.INFO)

# --- KONFIGURASI ---
CANISTER_ID = os.getenv("CANISTER_ID")
ICP_NETWORK_URL = os.getenv("ICP_NETWORK_URL") or os.getenv("ICP_REPLICA_URL")
AGENT_SEED = os.getenv("STORAGE_AGENT_SEED", "storage_agent_secret_seed")
IDENTITY_PATH = os.getenv("STORAGE_AGENT_KEY_PATH")

# Retry/backoff configuration
STORAGE_MAX_RETRIES = int(os.getenv("STORAGE_MAX_RETRIES", "3"))
STORAGE_BACKOFF_BASE = float(os.getenv("STORAGE_BACKOFF_BASE", "0.5"))

# Agent is created lazily to avoid import-time side-effects (local replica start)
agent = None


try:
    from uamodels import StoreChat
except Exception:
    # lightweight fallback
    class StoreChat:
        def __init__(self, entry_id: str | None = None, entry: str = ""):
            self.entry_id = entry_id
            self.entry = entry


async def initialize(ctx: Any):
    # kept for parity with the uagents lifecycle; will be called if an Agent is created
    if agent is not None:
        ctx.logger.info(f"StorageAgent address: {agent.address}")
    if ICAgent is None:
        ctx.logger.info("ic-py not available, StorageAgent will run in dry-run mode for on-chain calls.")
    else:
        ctx.logger.info("ic-py available: will attempt on-chain calls when ICP URL is configured.")


def encode_args_for_add(entry_id: str, entry: str) -> bytes:
    if encode is None:
        raise RuntimeError("ic-py candid encode not available")
    # Candid types: (text, text)
    return encode((entry_id, entry), "(text, text)")


async def call_add_chat_entry_direct(entry_id: str, entry: str) -> dict:
    """Directly call the canister using ic-py with retries and backoff.

    Returns a dict with keys: ok (bool), dry_run (bool, optional), result (raw
    response, optional), attempts (int), error (str, optional).

    If ICP_NETWORK_URL is not set, operates in dry-run mode.
    """
    # Resolve env at runtime so tests can monkeypatch
    # Resolve env at runtime so tests can monkeypatch. Treat an explicitly set
    # empty env var as 'unset' to allow tests to force dry-run by setting
    # ICP_NETWORK_URL="".
    env_icp = os.environ.get("ICP_NETWORK_URL", None)
    env_rep = os.environ.get("ICP_REPLICA_URL", None)
    if env_icp is not None:
        icp_network_url = env_icp.strip() or None
    elif env_rep is not None:
        icp_network_url = env_rep.strip() or None
    else:
        icp_network_url = ICP_NETWORK_URL or None

    canister_id = os.environ.get("CANISTER_ID", None) or CANISTER_ID

    # DEBUG: log resolved runtime env for troubleshooting tests
    logger.info("Resolved icp_network_url=%r, canister_id=%r, Client=%s", icp_network_url, canister_id, Client is not None)

    # If no network URL is configured we operate in dry-run regardless of canister id
    if not icp_network_url:
        logger.info("DRY RUN: would call canister %s with entry_id=%s", canister_id, entry_id)
        return {"ok": True, "dry_run": True, "attempts": 0}

    if not canister_id:
        logger.error("CANISTER_ID is not configured")
        return {"ok": False, "error": "CANISTER_ID not set"}

    if Client is None or ICAgent is None:
        logger.error("ic-py not available in environment")
        return {"ok": False, "error": "ic-py not installed in environment"}

    # build client and agent
    try:
        client = Client(url=icp_network_url)
    except Exception as e:
        logger.exception("Failed to construct ic client")
        return {"ok": False, "error": f"failed to construct client: {e}"}

    ic_agent = None
    if IDENTITY_PATH and BasicIdentity is not None:
        try:
            with open(IDENTITY_PATH, "rb") as f:
                key = f.read()
            identity = BasicIdentity.from_pem(key)
            ic_agent = ICAgent(identity, client)
        except Exception as e:
            logger.exception("Failed to load identity for ic-py agent")
            return {"ok": False, "error": f"failed to load identity: {e}"}
    else:
        # try anonymous agent if supported
        try:
            ic_agent = ICAgent(None, client)
        except Exception as e:
            logger.exception("Failed to create anonymous ic-py agent")
            return {"ok": False, "error": "unable to create ic-py agent; provide IDENTITY_PATH"}

    # encode and call with retries
    attempts = 0
    last_err = None
    while attempts <= STORAGE_MAX_RETRIES:
        attempts += 1
        try:
            args = encode_args_for_add(entry_id, entry)
            res = await ic_agent.update_raw(canister_id=CANISTER_ID, method_name="add_chat_entry", arg=args)
            logger.info("Successfully called canister add_chat_entry on attempt %d", attempts)
            return {"ok": True, "result": res, "attempts": attempts}
        except Exception as e:
            last_err = str(e)
            logger.exception("ic-py call failed on attempt %d", attempts)
            if attempts > STORAGE_MAX_RETRIES:
                logger.error("Exceeded max retries (%d) for canister call", STORAGE_MAX_RETRIES)
                return {"ok": False, "error": last_err, "attempts": attempts}
            # exponential backoff
            wait = STORAGE_BACKOFF_BASE * (2 ** (attempts - 1))
            logger.info("Retrying in %.2fs... (attempt %d of %d)", wait, attempts + 1, STORAGE_MAX_RETRIES)
            try:
                await asyncio.sleep(wait)
            except asyncio.CancelledError:
                logger.warning("Sleep interrupted during backoff")
                break



async def handle_store_chat(ctx: Any, sender: str, msg: StoreChat):
    ctx.logger.info("Received request to store entry: '%s' from %s", msg.entry, sender)

    entry_id = msg.entry_id or str(uuid.uuid4())

    # If ic-py is not available or ICP URL missing, just log and return (dry-run)
    # Resolve runtime env same as above and honor explicit empty string as unset
    env_icp = os.environ.get("ICP_NETWORK_URL", None)
    env_rep = os.environ.get("ICP_REPLICA_URL", None)
    if env_icp is not None:
        icp_network_url = env_icp.strip() or None
    elif env_rep is not None:
        icp_network_url = env_rep.strip() or None
    else:
        icp_network_url = ICP_NETWORK_URL or None

    if not icp_network_url or Client is None:
        ctx.logger.info("DRY RUN mode: not performing on-chain call. entry_id=%s", entry_id)
        return {"ok": True, "dry_run": True, "entry_id": entry_id}

    # perform on-chain write
    result = await call_add_chat_entry_direct(entry_id, msg.entry)
    if result.get("ok"):
        ctx.logger.info("Successfully wrote to on-chain memory (entry_id=%s) after %s attempts", entry_id, result.get("attempts"))
    else:
        ctx.logger.error("Failed to write to canister (entry_id=%s): %s", entry_id, result.get("error"))
    # return the result so in-process callers can inspect outcome
    return {**result, "entry_id": entry_id}


def health() -> dict:
    """Return a minimal health status for the storage agent module.

    This is used by tests and by the orchestrator fallback when running in-process.
    """
    return {"canister": CANISTER_ID, "icpy": Client is not None}


def _create_and_run():
    global agent
    from uagents import Agent
    agent = Agent(
        name="storage_agent",
        seed=AGENT_SEED,
    )
    agent.run()

if __name__ == "__main__":
    _create_and_run()