import sys
import types

# Minimal fake uagents for tests to avoid importing the heavy runtime which
# starts a local PocketIC replica in this environment.
class _FakeAgent:
    def __init__(self, *args, **kwargs):
        self.address = "agent_fake"
    async def send(self, dest, msg):
        return True

fake_uagents = types.SimpleNamespace(
    Agent=_FakeAgent,
    send=lambda agent, dest, msg: (_FakeAgent().send(dest, msg)),
)

# Insert before any test imports
sys.modules.setdefault("uagents", fake_uagents)
sys.modules.setdefault("uagents.agent", fake_uagents)
sys.modules.setdefault("uagents.context", fake_uagents)
sys.modules.setdefault("uagents.contrib", fake_uagents)
sys.modules.setdefault("uagents.contrib.protocols", fake_uagents)
sys.modules.setdefault("uagents.contrib.protocols.http", fake_uagents)
