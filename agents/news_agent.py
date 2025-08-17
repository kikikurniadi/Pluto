"""Stub NewsAgent: returns mocked news headlines for request text."""
def get_news(query: str) -> str:
    # naive stubbed response
    return "(stub) Tidak ada berita baru yang relevan untuk query Anda."
import os
import requests
from dotenv import load_dotenv
from typing import Any
from pydantic import BaseModel

# Muat variabel dari file .env
load_dotenv()

AGENT_SEED = os.getenv("NEWS_AGENT_SEED", "news_agent_secret_seed")
CRYPTO_PANIC_API_KEY = os.getenv("CRYPTO_PANIC_API_KEY")

# create Agent lazily to avoid import-time side-effects
agent = None

CRYPTO_PANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

class NewsRequest(BaseModel):
    topic: str  # contoh: "BTC" atau "ETH"


class NewsArticle(BaseModel):
    title: str
    url: str


class NewsResponse(BaseModel):
    articles: list[NewsArticle]
    success: bool
    error: str | None = None

async def initialize(ctx: Any):
    if agent is not None:
        ctx.logger.info(f"NewsAgent address: {agent.address}")


async def get_news(ctx: Any, sender: str, msg: NewsRequest):
    ctx.logger.info(f"Received news request for topic: {msg.topic}")

    if not CRYPTO_PANIC_API_KEY:
        error_msg = "CryptoPanic API key is not configured."
        ctx.logger.error(error_msg)
        await ctx.send(sender, NewsResponse(articles=[], success=False, error=error_msg))
        return

    try:
        params = {
            "auth_token": CRYPTO_PANIC_API_KEY,
            "currencies": msg.topic.upper(),
            "public": "true"
        }
        response = requests.get(CRYPTO_PANIC_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = [
            NewsArticle(title=post['title'], url=post['url'])
            for post in data.get('results', [])[:5] # Ambil 5 berita teratas
        ]

        await ctx.send(sender, NewsResponse(articles=articles, success=True))

    except requests.exceptions.RequestException as e:
        error_str = f"API call failed: {e}"
        ctx.logger.error(error_str)
        await ctx.send(sender, NewsResponse(articles=[], success=False, error=error_str))

if __name__ == "__main__":
    from uagents import Agent
    agent = Agent(name="news_agent", seed=AGENT_SEED)
    agent.run()