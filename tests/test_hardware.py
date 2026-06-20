"""Hardware abstraction tests."""

from __future__ import annotations

from src.hardware.sdr_controller import SDRController


def test_simulated_sdr_controller_returns_iq():
    iq = SDRController(simulated=True).read_iq(samples=128)
    assert iq.shape == (128, 2)
