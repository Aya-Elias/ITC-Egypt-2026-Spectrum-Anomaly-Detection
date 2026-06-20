"""Database CRUD tests."""

from __future__ import annotations

from src.database import crud


def test_signal_and_alert_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(crud, "DB_PATH", tmp_path / "spectrum.db")

    signal_id = crud.add_signal(
        label="Drone",
        confidence=0.91,
        frequency=2400.0,
        snr=12.5,
        source="unit-test",
        inference_time_ms=7,
        model_version="test",
    )
    alert_id = crud.auto_create_alert(signal_id, alert_type="email", location="Lab")

    signals = crud.get_all_signals()
    alerts = crud.get_all_alerts()

    assert signal_id == 1
    assert alert_id == 1
    assert signals[0]["label"] == "Drone"
    assert alerts[0]["location"] == "Lab"


def test_normal_signal_does_not_create_alert(tmp_path, monkeypatch):
    monkeypatch.setattr(crud, "DB_PATH", tmp_path / "spectrum.db")
    signal_id = crud.add_signal("Normal", 0.99, None, None, "unit-test", 4, "test")
    assert crud.auto_create_alert(signal_id, "email", "Lab") is None
