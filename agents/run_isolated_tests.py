"""Run a couple of unit tests in-process while faking the heavy `uagents` package.
This avoids pytest collection and the environment that starts PocketIC.

Usage: python run_isolated_tests.py
"""
import sys
import types
import asyncio

# Create a minimal fake `uagents` package using ModuleType so the import system
# treats it like a real package and won't try to load submodules from disk.
class FakeAgent:
    def __init__(self, *args, **kwargs):
        self.address = "agent_fake"
    async def send(self, dest, msg):
        return True

def fake_send(agent, dest, msg):
    return asyncio.run(FakeAgent().send(dest, msg))

def make_module(name: str):
    m = types.ModuleType(name)
    return m

# base package
mod_uagents = make_module('uagents')
mod_uagents.Agent = FakeAgent
mod_uagents.send = fake_send

# common submodules some code imports directly
mod_uagents_agent = make_module('uagents.agent')
mod_uagents_agent.Agent = FakeAgent
mod_uagents_context = make_module('uagents.context')
mod_uagents_contrib = make_module('uagents.contrib')
mod_uagents_contrib_protocols = make_module('uagents.contrib.protocols')
mod_http = make_module('uagents.contrib.protocols.http')
mod_http.Httpy = lambda ctx: None

# inject before importing test modules
sys.modules['uagents'] = mod_uagents
sys.modules['uagents.agent'] = mod_uagents_agent
sys.modules['uagents.context'] = mod_uagents_context
sys.modules['uagents.contrib'] = mod_uagents_contrib
sys.modules['uagents.contrib.protocols'] = mod_uagents_contrib_protocols
sys.modules['uagents.contrib.protocols.http'] = mod_http

print('Inserted fake uagents into sys.modules')

# Run orchestrator test
print('\n== running orchestrator_simple test ==')
import orchestrator_simple as orch

from fastapi.testclient import TestClient
client = TestClient(orch.app)
resp = client.post('/query', json={'text': 'berapa harga bitcoin'})
print('orchestrator status:', resp.status_code, 'json:', resp.json())

# Run storage_agent tests (async)
print('\n== running storage_agent dry-run test ==')
import storage_agent as sa

async def run_storage_tests():
    # ensure ICP_NETWORK_URL is empty for dry-run
    import os
    os.environ['ICP_NETWORK_URL'] = ''
    res = await sa.call_add_chat_entry_direct('id-1', 'hello')
    print('storage_agent.call_add_chat_entry_direct ->', res)

asyncio.run(run_storage_tests())
print('\nDone')
