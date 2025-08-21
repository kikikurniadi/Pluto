"""Stub PriceAgent: returns a mocked current price for a symbol."""
def get_price(symbol: str) -> str:
    # Simple deterministic stub
    if symbol.lower() in ("btc", "bitcoin"):
        return "$65,000"
    if symbol.lower() in ("eth", "ethereum"):
        return "$3,500"
    return "unknown"
import os
import requests
from typing import Any
from pydantic import BaseModel

AGENT_SEED = os.getenv("PRICE_AGENT_SEED", "price_agent_secret_seed")

# create Agent lazily
agent = None

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"


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
    try:
        params = {"ids": msg.coin_id, "vs_currencies": "usd"}
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()

        price = data.get(msg.coin_id, {}).get("usd")
        if price:
            await ctx.send(sender, PriceResponse(price=price, currency="usd", success=True))
        else:
            await ctx.send(sender, PriceResponse(price=0.0, currency="usd", success=False, error="Coin not found"))

    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"API call failed: {e}")
        await ctx.send(sender, PriceResponse(price=0.0, currency="usd", success=False, error=str(e)))

if __name__ == "__main__":
    from uagents import Agent
    agent = Agent(name="price_agent", seed=AGENT_SEED)
    agent.run()