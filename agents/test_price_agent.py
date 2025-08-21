import json
from unittest.mock import patch, Mock

import pytest

import price_agent as pa


def test_get_price_success(monkeypatch):
    fake_json = {"bitcoin": {"usd": 65000}}

    mock_resp = Mock()
    mock_resp.json.return_value = fake_json
    mock_resp.raise_for_status.return_value = None

    with patch("price_agent.requests.get", return_value=mock_resp) as p:
        s = pa.get_price("bitcoin")
        assert s.startswith("$")
        assert "65000" in s.replace(",", "")


def test_get_price_failure(monkeypatch):
    # Simulate requests raising an exception
    with patch("price_agent.requests.get", side_effect=Exception("boom")):
        s = pa.get_price("bitcoin")
        assert s == "unknown"
