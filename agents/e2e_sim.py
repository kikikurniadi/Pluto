"""E2E simulator (in-process) for Orchestrator -> StorageAgent flow.
This does not require a local replica. It constructs the same message the
orchestrator would produce and calls the storage handler directly to exercise
the call path (dry-run if ICP not configured).
"""
import asyncio
import os
from dotenv import load_dotenv

# Ensure env is loaded the same way agents expect
load_dotenv()

from uamodels import StoreChat
import uuid
import logging


class DummyCtx:
    """Minimal context object with a logger compatible with uagents Context.logger
    used only for local in-process simulation.
    """
    def __init__(self):
        self.logger = logging.getLogger("e2e_ctx")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = logging.Formatter("%(levelname)s: [e2e_ctx] %(message)s")
            handler.setFormatter(fmt)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)


async def run_once(text: str):
    entry_id = str(uuid.uuid4())
    entry = f"Q: {text} -- A: (simulated reply)"
    msg = StoreChat(entry_id=entry_id, entry=entry)

    print("Simulating orchestrator -> storage_agent message")
    print(f"entry_id={entry_id}")
    # Call the registered handler directly
    ctx = DummyCtx()
    try:
        # import storage_agent lazily to avoid import-time side-effects
        import storage_agent
        await storage_agent.handle_store_chat(ctx, "orchestrator_simple", msg)
    except Exception as e:
        print("Handler raised:", e)

    # Also call the low-level canister call function to see dry-run output/result
    try:
        if hasattr(storage_agent, "call_add_chat_entry_direct"):
            res = await storage_agent.call_add_chat_entry_direct(entry_id, entry)
            print("call_add_chat_entry_direct ->", res)
    except Exception as e:
        print("call_add_chat_entry_direct raised:", e)


def main():
    text = os.environ.get("E2E_TEXT", "berapa harga bitcoin")
    asyncio.run(run_once(text))


if __name__ == "__main__":
    main()
