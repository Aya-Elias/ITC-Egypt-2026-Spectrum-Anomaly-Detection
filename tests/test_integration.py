"""Lightweight integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


def test_api_docs_and_agent_health_smoke():
    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    response = client.get("/api/v1/agent/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
