"""Tests for RF model loading and prediction helpers.

TensorFlow is optional in the default developer environment. These tests are
marked as ``ml`` and skipped cleanly when TensorFlow is unavailable.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

pytestmark = pytest.mark.ml

tf = pytest.importorskip("tensorflow")

from src.ai_model.predict import load_model_and_params, predict_single  # noqa: E402


MODEL_PATH = "src/ai_model/saved_models/best_model.keras"
NORM_PATH = "src/ai_model/saved_models/norm_params.npy"


def test_model_artifacts_exist():
    assert os.path.exists(MODEL_PATH)
    assert os.path.exists(NORM_PATH)


def test_model_loading_and_prediction_shape():
    model, min_val, max_val = load_model_and_params(MODEL_PATH, NORM_PATH)
    dummy_input = np.random.default_rng(42).integers(0, 255, (224, 224, 3), dtype=np.uint8)
    result = predict_single(model, dummy_input, min_val, max_val)

    assert result["class_name"] in {"Drone", "Normal", "Jamming"}
    assert 0 <= result["confidence"] <= 1
    assert pytest.approx(sum(result["probabilities"].values()), abs=1e-5) == 1.0
    assert model.output_shape[-1] == 3
