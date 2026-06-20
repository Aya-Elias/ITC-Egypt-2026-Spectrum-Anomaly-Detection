"""API smoke tests for SADAR FastAPI routes."""

from __future__ import annotations

import importlib

import numpy as np
from fastapi.testclient import TestClient

from src.api.main import app


class FakeModel:
    input_shape = (None, 224, 224, 3)
    output_shape = (None, 3)

    def predict(self, _x, verbose=0):
        return np.array([[0.05, 0.10, 0.85]], dtype=np.float32)


def test_root_and_health_endpoints():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/agent/health").status_code == 200


def test_predict_with_fake_model_and_temp_db(tmp_path):
    crud = importlib.import_module("crud")
    crud.DB_PATH = tmp_path / "spectrum.db"
    app.state.model = FakeModel()
    app.state.model_version = "test"

    client = TestClient(app)
    payload = {
        "spectrogram": np.zeros((224, 224, 3), dtype=np.float32).tolist(),
        "frequency": 2450.0,
        "snr": 18.0,
        "source": "pytest",
        "alert_type": "email",
        "location": "Test range",
    }
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Jamming"
    assert body["alert_triggered"] is True
    assert body["model_version"] == "test"
