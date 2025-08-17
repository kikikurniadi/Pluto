"""Lightweight shim for uagents used only for local testing in this workspace.
This shadows the installed heavy `uagents` package by existing in the repo root
and being importable first (workspace is in sys.path when running tests in VS Code).

The shim implements minimal Agent, send, and a tiny context object to satisfy
imports used by the agents in this repo.
"""
from types import SimpleNamespace
import asyncio

class Agent:
    def __init__(self, *args, **kwargs):
        self.address = "agent://local/shim"
        self.ctx = SimpleNamespace(logger=SimpleNamespace(info=lambda *a, **k: None), send=self.send)
    def run(self):
        # no-op for shim
        return
    async def send(self, dest, message):
        return True

async def send(agent, dest, message):
    return await Agent().send(dest, message)

# Minimal export names
__all__ = ['Agent', 'send']
