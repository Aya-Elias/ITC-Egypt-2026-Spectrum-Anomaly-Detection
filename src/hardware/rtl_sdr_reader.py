"""RTL-SDR reader abstraction.

The real pyrtlsdr dependency is optional so the project can be tested on CI
machines without SDR hardware attached.
"""

from __future__ import annotations

import numpy as np

from .hardware_config import SDRConfig


class RTLSDRUnavailable(RuntimeError):
    """Raised when RTL-SDR hardware/dependency is unavailable."""


class RTLSDRReader:
    def __init__(self, config: SDRConfig | None = None):
        self.config = config or SDRConfig()

    def read_samples(self, count: int = 1024) -> np.ndarray:
        """Read I/Q samples from hardware.

        This placeholder intentionally fails clearly until pyrtlsdr integration is
        enabled on a machine with an attached SDR.
        """
        raise RTLSDRUnavailable("RTL-SDR hardware integration is not configured in this environment")
