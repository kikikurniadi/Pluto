"""Re-export shim for `agents` modules under `uagents.agents`.

This module lazy-imports the real modules from the top-level `agents`
package (or flat folder) and exposes them so existing code can import
`uagents.agents.orchestrator_agent` instead of `agents.orchestrator_agent`.

It avoids importing heavy dependencies at module import time by performing
the import only when attributes are accessed.
"""
import importlib
from types import ModuleType
from typing import Any, Optional


class _LazyModule(ModuleType):
    def __init__(self, module_name: str):
        super().__init__(module_name)
        self.__module_name = module_name
        self.__real_module: Optional[ModuleType] = None

    def _load(self) -> ModuleType:
        if self.__real_module is None:
            self.__real_module = importlib.import_module(self.__module_name)
        return self.__real_module

    def __getattr__(self, name: str) -> Any:
        mod = self._load()
        return getattr(mod, name)


# Provide lazy proxies for the main agent modules we expect callers to use.
_modules = [
    "agents.orchestrator_agent",
    "agents.storage_agent",
    "agents.news_agent",
    "agents.price_agent",
    "agents.orchestrator_simple",
]

for m in _modules:
    short = m.split(".")[-1]
    globals()[short] = _LazyModule(m)

__all__ = [m.split(".")[-1] for m in _modules]
