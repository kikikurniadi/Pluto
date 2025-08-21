"""Demo script: fetch price and attempt to store it via storage_agent.

Usage:
  python agents/fetch_and_store_demo.py --symbol bitcoin

By default it will run in dry-run mode unless `ICP_NETWORK_URL` and `CANISTER_ID`
are configured in the environment.
"""
import argparse
import asyncio
import os

from price_agent import get_price

import importlib


async def main(symbol: str):
    price = get_price(symbol)
    print(f"Fetched price for {symbol}: {price}")

    # import storage_agent lazily
    sa = importlib.import_module("storage_agent")

    class Ctx:
        def __init__(self):
            import logging
            self.logger = logging.getLogger("fetch_and_store_demo")

        async def send(self, to, msg):
            return True

    msg = None
    from uamodels import StoreChat
    entry_id = None
    entry_text = f"Demo price {symbol}: {price}"
    sc = StoreChat(entry_id=None, entry=entry_text)

    print("Calling storage_agent.handle_store_chat (may be dry-run)...")
    res = await sa.handle_store_chat(Ctx(), "demo", sc)
    print("Storage result:", res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="bitcoin")
    args = parser.parse_args()
    asyncio.run(main(args.symbol))
