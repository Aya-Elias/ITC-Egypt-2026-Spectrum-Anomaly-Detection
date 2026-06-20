"""Signal-processing tests."""

from __future__ import annotations

import numpy as np

from src.signal_processing.iq_processor import iq_to_model_image
from src.signal_processing.signal_generator import generate_iq_tone
from src.signal_processing.stft import compute_stft_spectrogram


def test_iq_to_spectrogram_and_model_image():
    iq = generate_iq_tone(samples=512)
    spec = compute_stft_spectrogram(iq, nfft=128, hop_length=64)
    image = iq_to_model_image(iq)

    assert spec.ndim == 2
    assert image.shape == (224, 224, 3)
    assert image.dtype == np.uint8


def test_invalid_iq_shape_rejected():
    with np.testing.assert_raises(ValueError):
        compute_stft_spectrogram(np.zeros((128,), dtype=np.float32))
