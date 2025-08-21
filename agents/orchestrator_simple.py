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
from typing import Optional
from fastapi import Depends, Header, HTTPException, status, Request
from pydantic import BaseModel

# Scheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except Exception:
    AsyncIOScheduler = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator_simple")

app = FastAPI()
# create agent lazily to avoid import-time side-effects
agent = None

# Scheduler instance (created lazily)
scheduler: Optional[AsyncIOScheduler] = None


class ScheduleIn(BaseModel):
    symbol: str = "bitcoin"
    interval_seconds: int = 60


class RotateIn(BaseModel):
    new_token: str


def _ensure_scheduler():
    global scheduler
    if AsyncIOScheduler is None:
        raise RuntimeError("APScheduler not installed")
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()


def _check_schedule_token(authorization: Optional[str] = Header(None), x_scheduler_token: Optional[str] = Header(None)):
    """Require a bearer token via Authorization header or X-Scheduler-Token header when SCHEDULE_TOKEN is set.

    The token is read from the environment on every request so admins can rotate
    the token without restarting the process.
    """
    # Token resolution order:
    # 1. If a token file exists, read it (persisted token)
    # 2. Else read SCHEDULE_TOKEN env var
    configured = ""
    token_file = os.environ.get("SCHEDULE_TOKEN_FILE", "./.schedule_token")
    try:
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                configured = f.read().strip()
    except Exception:
        configured = ""
    if not configured:
        configured = os.environ.get("SCHEDULE_TOKEN", "")
    # If no token configured, skip auth
    if not configured:
        return True

    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization
    if not token and x_scheduler_token:
        token = x_scheduler_token

    if token != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid schedule token")
    return True


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


@app.get("/health")
async def health_endpoint():
    """Simple health check for the orchestrator service."""
    return {"status": "ok", "agent": getattr(agent, "address", None)}


async def _scheduled_fetch_and_store(symbol: str):
    """Job: fetch price and call storage_agent.handle_store_chat in-process."""
    try:
        price = get_price(symbol)
        entry_id = str(uuid.uuid4())
        entry = f"Scheduled price {symbol}: {price}"
        msg = StoreChat(entry_id=entry_id, entry=entry)

        # call storage_agent in-process if available
        try:
            import storage_agent as sa

            class Ctx:
                def __init__(self):
                    import logging
                    self.logger = logging.getLogger("orchestrator_scheduler")

                async def send(self, to, msg):
                    return True

            await sa.handle_store_chat(Ctx(), "orchestrator_scheduler", msg)
        except Exception:
            logger.exception("Scheduled fetch_and_store failed to call storage_agent")
    except Exception:
        logger.exception("Scheduled job failed")


@app.post("/schedule/start")
async def schedule_start(s: ScheduleIn, request: Request, _auth=Depends(_check_schedule_token)):
    """Start a periodic scheduled job that fetches price and stores it."""
    _ensure_scheduler()
    job_id = "fetch_and_store"
    # avoid duplicate jobs
    if scheduler.get_job(job_id):
        return {"ok": False, "error": "job already running"}

    scheduler.add_job(_scheduled_fetch_and_store, "interval", seconds=s.interval_seconds, args=[s.symbol], id=job_id)
    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    logger.info("Scheduled job started: symbol=%s interval=%s by %s ua=%s", s.symbol, s.interval_seconds, client_ip, ua)
    return {"ok": True, "job_id": job_id}


@app.post("/schedule/stop")
async def schedule_stop(request: Request, _auth=Depends(_check_schedule_token)):
    _ensure_scheduler()
    job_id = "fetch_and_store"
    job = scheduler.get_job(job_id)
    if not job:
        return {"ok": False, "error": "no job found"}
    scheduler.remove_job(job_id)
    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    logger.info("Scheduled job stopped by %s ua=%s", client_ip, ua)
    return {"ok": True}


@app.get("/schedule/status")
async def schedule_status(request: Request, _auth=Depends(_check_schedule_token)):
    if AsyncIOScheduler is None:
        return {"ok": False, "error": "APScheduler not installed"}
    if scheduler is None:
        return {"ok": True, "running": False}
    job = scheduler.get_job("fetch_and_store")
    client_ip = request.client.host if request.client else None
    logger.info("Schedule status requested by %s", client_ip)
    if not job:
        return {"ok": True, "running": False}

    # Try to surface next run time and trigger interval if available
    next_run = None
    try:
        nr = job.next_run_time
        if nr is not None:
            # ISO format for JSON
            next_run = nr.isoformat()
    except Exception:
        next_run = None

    # APScheduler job trigger details may include interval seconds
    interval_seconds = None
    try:
        trigger = getattr(job, "trigger", None)
        if trigger is not None and hasattr(trigger, "interval"):
            interval_seconds = getattr(trigger.interval, "seconds", None)
    except Exception:
        interval_seconds = None

    return {"ok": True, "running": True, "next_run_time": next_run, "interval_seconds": interval_seconds}


@app.post("/schedule/rotate")
async def schedule_rotate(r: RotateIn, request: Request, _auth=Depends(_check_schedule_token)):
    """Rotate the in-memory schedule token. This updates os.environ['SCHEDULE_TOKEN'] for the running process.

    Note: this change is not persisted to disk; it affects only the current process.
    """
    # Persist the new token to configured token file (default ./.schedule_token)
    token_file = os.environ.get("SCHEDULE_TOKEN_FILE", "./.schedule_token")
    old = None
    try:
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                old = f.read().strip()
    except Exception:
        old = None

    try:
        # write token atomically and set restrictive permissions
        tmp_path = token_file + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(r.new_token or "")
        try:
            os.chmod(tmp_path, 0o600)
        except Exception:
            pass
        os.replace(tmp_path, token_file)
    except Exception:
        # Fall back to in-memory env var if file write fails
        os.environ["SCHEDULE_TOKEN"] = r.new_token or ""

    client_ip = request.client.host if request.client else None
    logger.info("Schedule token rotated by %s (old set=%s) persisted_to=%s", client_ip, bool(old), token_file)

    # append audit log entry (timestamp, ip, old-present)
    try:
        audit_path = os.environ.get("SCHEDULE_TOKEN_AUDIT", "./.schedule_token_audit.log")
        with open(audit_path, "a") as af:
            import datetime
            ts = datetime.datetime.utcnow().isoformat() + "Z"
            af.write(f"{ts} ip={client_ip} old_present={bool(old)} path={token_file}\n")
    except Exception:
        logger.exception("Failed to append schedule token audit log")

    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
    # if executed directly, create agent and run normally
    from uagents import Agent
    agent = Agent(name="orchestrator_simple", seed=os.getenv("ORCHESTRATOR_SEED", "orch_seed"))
