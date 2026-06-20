"""Dashboard module smoke tests."""

from __future__ import annotations

from src.dashboard import utils


def test_dashboard_api_helper_builds_url(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(utils.requests, "get", fake_get)
    assert utils.api_get("http://api/", "/health") == {"ok": True}
    assert captured == {"url": "http://api/health", "timeout": 5}
