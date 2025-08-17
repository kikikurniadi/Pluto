import os
import sys
import uuid
import logging
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
    """Directly call the canister using ic-py. Returns dict with result or error.
    If ICP_NETWORK_URL is not set, operates in dry-run mode.
    """
    if not CANISTER_ID:
        return {"ok": False, "error": "CANISTER_ID not set"}

    if not ICP_NETWORK_URL:
        logger.info("DRY RUN: would call canister %s with entry_id=%s", CANISTER_ID, entry_id)
        return {"ok": True, "dry_run": True}

    if Client is None or ICAgent is None:
        return {"ok": False, "error": "ic-py not installed in environment"}

    # build client and agent
    client = Client(url=ICP_NETWORK_URL)

    ic_agent = None
    if IDENTITY_PATH and BasicIdentity is not None:
        try:
            with open(IDENTITY_PATH, "rb") as f:
                key = f.read()
            identity = BasicIdentity.from_pem(key)
            ic_agent = ICAgent(identity, client)
        except Exception as e:
            return {"ok": False, "error": f"failed to load identity: {e}"}
    else:
        # try anonymous agent if supported
        try:
            ic_agent = ICAgent(None, client)
        except Exception:
            return {"ok": False, "error": "unable to create ic-py agent; provide IDENTITY_PATH"}

    # encode and call
    try:
        args = encode_args_for_add(entry_id, entry)
        res = await ic_agent.update_raw(canister_id=CANISTER_ID, method_name="add_chat_entry", arg=args)
        return {"ok": True, "result": res}
    except Exception as e:
        logger.exception("ic-py call failed")
        return {"ok": False, "error": str(e)}


async def handle_store_chat(ctx: Any, sender: str, msg: StoreChat):
    ctx.logger.info(f"Received request to store entry: '{msg.entry}' from {sender}")

    entry_id = msg.entry_id or str(uuid.uuid4())

    # If ic-py is not available or ICP URL missing, just log and return
    if not ICP_NETWORK_URL or Client is None:
        ctx.logger.info("DRY RUN mode: not performing on-chain call. entry_id=%s", entry_id)
        return

    # perform on-chain write
    result = await call_add_chat_entry_direct(entry_id, msg.entry)
    if result.get("ok"):
        ctx.logger.info("Successfully wrote to on-chain memory (entry_id=%s)", entry_id)
    else:
        ctx.logger.error("Failed to write to canister: %s", result.get("error"))


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