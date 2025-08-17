"""Lightweight Orchestrator skeleton (simple REST) that sends StoreChat to storage_agent via uagents send().
This coexists with the existing orchestrator_agent.py file.
"""
import os
import uuid
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from uamodels import StoreChat
from price_agent import get_price
from news_agent import get_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator_simple")

app = FastAPI()
# create agent lazily to avoid import-time side-effects
agent = None


class QueryIn(BaseModel):
    text: str


@app.post("/query")
async def query_endpoint(q: QueryIn):
    text = q.text
    # naive intent parsing + delegate to stub agents
    if any(w in text.lower() for w in ["harga", "price"]):
        # try to extract symbol
        symbol = "btc"
        for s in ["btc", "bitcoin", "eth", "ethereum"]:
            if s in text.lower():
                symbol = s
                break
        reply = f"Harga {symbol.upper()} saat ini adalah {get_price(symbol)}"
    elif any(w in text.lower() for w in ["berita", "news"]):
        reply = get_news(text)
    else:
        reply = "Maaf, saya tidak mengerti."

    entry_id = str(uuid.uuid4())
    msg = StoreChat(entry_id=entry_id, entry=f"Q: {text} -- A: {reply}")
    # send to storage_agent (non-blocking)
    async def _send(dest, message):
        # prefer agent.send if available
        send_fn = getattr(agent, "send", None) if agent is not None else None
        if send_fn:
            return await send_fn(dest, message)
        # fall back to uagents.send if available (lazy import)
        try:
            import uagents as _uagents_module
            send_mod_fn = getattr(_uagents_module, "send", None)
            if send_mod_fn:
                return await send_mod_fn(agent, dest, message)
        except Exception:
            pass
        # neither available
        raise RuntimeError("no send API available on Agent or uagents module")

    try:
        await _send("storage_agent", msg)
    except Exception as e:
        logger.exception("Failed to send StoreChat")
        return {"error": "storage send failed"}

    return {"reply": reply, "entry_id": entry_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
    # if executed directly, create agent and run normally
    from uagents import Agent
    agent = Agent(name="orchestrator_simple", seed=os.getenv("ORCHESTRATOR_SEED", "orch_seed"))
