"""Stub PriceAgent: returns a mocked current price for a symbol."""
"""Price agent helpers.

This module exposes a synchronous `get_price(symbol)` helper used by the
lightweight orchestrator. It uses CoinGecko's simple price API and returns a
formatted USD string (e.g. "$65,000.00") or "unknown" on error.

The module also contains a small async handler (kept for parity) but the
main integration for the orchestrator is `get_price()`.
"""
import os
from typing import Any

import requests

AGENT_SEED = os.getenv("PRICE_AGENT_SEED", "price_agent_secret_seed")

# create Agent lazily (kept for compatibility with uagents runtime)
agent = None

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# common symbol mapping to CoinGecko ids
SYMBOL_TO_ID = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
}


def _format_usd(amount: float) -> str:
    try:
        return f"${amount:,.2f}"
    except Exception:
        return str(amount)


def get_price(symbol: str, vs_currency: str = "usd") -> str:
    """Return formatted price string for a symbol using CoinGecko.

    Returns 'unknown' when the coin or API call fails.
    """
    if not symbol:
        return "unknown"

    coin_id = SYMBOL_TO_ID.get(symbol.lower())
    if coin_id is None:
        # Best-effort: accept coin_id directly if user passed it
        coin_id = symbol.lower()

    try:
        params = {"ids": coin_id, "vs_currencies": vs_currency}
        resp = requests.get(COINGECKO_API_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        price = data.get(coin_id, {}).get(vs_currency)
        if price is None:
            return "unknown"
        # Format as USD-like string when numeric
        if isinstance(price, (int, float)):
            return _format_usd(float(price))
        return str(price)
    except Exception:
        return "unknown"


# Async handler left for uagents integration (kept simple)
from pydantic import BaseModel


class PriceRequest(BaseModel):
    coin_id: str


class PriceResponse(BaseModel):
    price: float
    currency: str
    success: bool
    error: str | None = None


async def startup(ctx: Any):
    if agent is not None:
        ctx.logger.info(f"PriceAgent address: {agent.address}")


async def handle_price_request(ctx: Any, sender: str, msg: PriceRequest):
    ctx.logger.info(f"Received price request for: {msg.coin_id}")
    price_str = get_price(msg.coin_id)
    try:
        if price_str == "unknown":
            await ctx.send(sender, PriceResponse(price=0.0, currency="usd", success=False, error="not found"))
        else:
            # attempt to coerce numeric value from formatted string
            num = float(price_str.replace("$", "").replace(",", ""))
            await ctx.send(sender, PriceResponse(price=num, currency="usd", success=True))
    except Exception:
        await ctx.send(sender, PriceResponse(price=0.0, currency="usd", success=False, error="parse error"))


if __name__ == "__main__":
    from uagents import Agent
    agent = Agent(name="price_agent", seed=AGENT_SEED)
    agent.run()