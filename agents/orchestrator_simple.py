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
        global agent
        # prefer agent.send if available
        send_fn = getattr(agent, "send", None) if agent is not None else None
        if send_fn:
            return await send_fn(dest, message)

        # If agent not created, try to instantiate uagents.Agent from module (test provides a fake Agent)
        try:
            import uagents as _uagents_module
            AgentClass = getattr(_uagents_module, "Agent", None)
            if AgentClass and agent is None:
                # create global agent instance
                agent = AgentClass()
                send_fn = getattr(agent, "send", None)
                if send_fn:
                    return await send_fn(dest, message)
            # fall back to module-level send function if present
            send_mod_fn = getattr(_uagents_module, "send", None)
            if send_mod_fn:
                return await send_mod_fn(agent, dest, message)
        except Exception:
            pass

        # Fallback: try HTTP submit to storage agent (useful if other uagents APIs are not available)
        try:
            # if storage_agent module is available locally, call its handler directly (in-process)
            if dest == "storage_agent":
                try:
                    import storage_agent as sa
                    # create a fake ctx with logger and send
                    class Ctx:
                        def __init__(self):
                            import logging
                            self.logger = logging.getLogger("orchestrator_simple")

                        async def send(self, to, msg):
                            return True

                    ctx = Ctx()
                    # call handler directly
                    if hasattr(sa, "handle_store_chat"):
                        await sa.handle_store_chat(ctx, getattr(agent, "address", "orchestrator_simple"), message)
                        return True
                except Exception:
                    pass
            # fallback to HTTP POST if storage agent is running as a server
            import requests
            submit_url = "http://127.0.0.1:8000/submit"
            payload = {
                "destination": dest,
                "message": {"entry_id": getattr(message, "entry_id", None), "entry": getattr(message, "entry", None)},
                "sender": getattr(agent, "address", "orchestrator_simple")
            }
            resp = requests.post(submit_url, json=payload, timeout=2)
            if resp.status_code in (200, 202):
                return True
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
