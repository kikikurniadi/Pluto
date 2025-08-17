import os
from dotenv import load_dotenv
from typing import Any
from pydantic import BaseModel

# avoid importing uagents at module import time; will lazy-import when running
Httpy = None
HttpyRequest = None
HttpyResponse = None

# Muat variabel dari file .env
load_dotenv()

# --- KONFIGURASI ---
AGENT_SEED = os.getenv("ORCHESTRATOR_AGENT_SEED", "orchestrator_agent_secret_seed")
PRICE_AGENT_ADDRESS = os.getenv("PRICE_AGENT_ADDRESS")
NEWS_AGENT_ADDRESS = os.getenv("NEWS_AGENT_ADDRESS")
STORAGE_AGENT_ADDRESS = os.getenv("STORAGE_AGENT_ADDRESS")

# --- Model Pesan untuk Komunikasi Antar Agen ---
# Definisikan ulang di sini agar Orchestrator tahu formatnya
class PriceRequest(BaseModel):
    coin_id: str


class PriceResponse(BaseModel):
    price: float
    currency: str
    success: bool
    error: str | None = None


class NewsRequest(BaseModel):
    topic: str


class NewsResponse(BaseModel):
    articles: list
    success: bool
    error: str | None = None


class StoreChat(BaseModel):
    entry: str

# Inisialisasi Agen Orchestrator
agent = None

# httpy will be created if/when the agent is instantiated
httpy = None

async def initialize(ctx: Any):
    if agent is not None:
        ctx.logger.info(f"Orchestrator Agent running at: http://127.0.0.1:8000")
        ctx.logger.info(f"Orchestrator Agent Address: {agent.address}")

# Ini adalah endpoint yang akan diakses oleh frontend React
async def handle_query(request: Any, ctx: Any):
    data = request.json
    user_query = data.get("text", "").lower()
    ctx.logger.info(f"Received query from frontend: {user_query}")

    response_text = ""

    # Logika parsing maksud (intent parsing) sederhana
    if "harga" in user_query:
        try:
            # Ekstrak nama koin dari query
            coin = user_query.split("harga", 1)[1].strip()
            if coin and PRICE_AGENT_ADDRESS:
                ctx.logger.info(f"Intent: 'price', Entity: '{coin}'")
                # Kirim pesan ke PriceAgent dan tunggu respons
                price_response: PriceResponse = await ctx.query(
                    destination=PRICE_AGENT_ADDRESS,
                    message=PriceRequest(coin_id=coin),
                    timeout=15.0
                )
                if price_response.success:
                    response_text = f"Harga {coin.capitalize()} saat ini adalah ${price_response.price} USD."
                else:
                    response_text = f"Maaf, saya tidak dapat menemukan harga untuk {coin}."
            else:
                response_text = "Mohon sebutkan nama koin yang ingin Anda ketahui harganya."
        except Exception as e:
            response_text = f"Terjadi kesalahan saat memproses permintaan harga: {e}"

    elif "berita" in user_query:
        try:
            # Ekstrak topik berita dari query
            topic = user_query.split("berita", 1)[1].strip()
            if topic and NEWS_AGENT_ADDRESS:
                ctx.logger.info(f"Intent: 'news', Entity: '{topic}'")
                # Kirim pesan ke NewsAgent dan tunggu respons
                news_response: NewsResponse = await ctx.query(
                    destination=NEWS_AGENT_ADDRESS,
                    message=NewsRequest(topic=topic),
                    timeout=20.0
                )
                if news_response.success and news_response.articles:
                    # Format beberapa judul berita
                    titles = [f"- {article.get('title')}" for article in news_response.articles]
                    response_text = f"Berikut adalah berita teratas tentang {topic.upper()}:\n" + "\n".join(titles)
                else:
                    response_text = f"Maaf, saya tidak dapat menemukan berita tentang {topic}."
            else:
                response_text = "Mohon sebutkan topik berita yang ingin Anda cari."
        except Exception as e:
            response_text = f"Terjadi kesalahan saat memproses permintaan berita: {e}"

    else:
        response_text = "Maaf, saya tidak mengerti. Anda bisa bertanya tentang 'harga' atau 'berita' mata uang kripto."

    # Simpan jejak percakapan ke on-chain memory (jika ada)
    if STORAGE_AGENT_ADDRESS:
        chat_entry = f"User: '{user_query}' | Pluto: '{response_text}'"
        await ctx.send(STORAGE_AGENT_ADDRESS, StoreChat(entry=chat_entry))

    # Kirim respons kembali ke frontend
    return HttpyResponse(
        status_code=200,
        json={"response": response_text}
    )

if __name__ == "__main__":
    from uagents import Agent
    from uagents.contrib.protocols.http import Httpy

    agent = Agent(
        name="orchestrator_agent",
        seed=AGENT_SEED,
        port=8000,
        endpoint=["http://127.0.0.1:8000/submit"],
    )
    httpy = Httpy(agent.ctx)
    agent.run()