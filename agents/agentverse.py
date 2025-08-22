"""
POC AgentVerse integration client (offline/mock).

This module provides a minimal, local-only client shim for AgentVerse.ai to be used
in development and demos. It does NOT call any external service.

Behavior:
- `query(text)` returns a dict { summary, sources } where `summary` is a short
  synthetic answer and `sources` is a list of mock source dicts. The summary is
  deterministic (sha256 of text) so tests/demo flows are reproducible.

Replace this with a real HTTP client when integrating with agentverse.ai API.
"""
from __future__ import annotations
import hashlib
from typing import Dict, List


class AgentVerseClient:
    """Minimal deterministic client for demo/testing.

    Usage:
      client = AgentVerseClient()
      res = client.query("What is the price of BTC?")
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _deterministic_summary(self, text: str) -> str:
        # simple deterministic summary: first 120 chars + hash suffix
        h = hashlib.sha256(text.encode()).hexdigest()[:8]
        short = (text.strip().replace("\n", " ")[:120]).strip()
        return f"{short} — (agentverse-poc:{h})"

    def _mock_sources(self, text: str) -> List[Dict[str, str]]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return [
            {"url": f"https://example.com/source/{h[:8]}", "title": "Mock Source", "excerpt": text[:200]},
        ]

    def query(self, text: str) -> Dict[str, object]:
        summary = self._deterministic_summary(text)
        sources = self._mock_sources(text)
        return {"summary": summary, "sources": sources}
