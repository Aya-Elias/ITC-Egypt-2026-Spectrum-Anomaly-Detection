"""
src/ai_model/__init__.py
------------------------
Makes the ai_model directory a Python package.
Exposes the main functions for easy import.
"""

from .predict import load_model_and_params, predict_single, predict_batch
from .model_loader import load_model, load_norm_params, load_all
from .data_preprocessing import preprocess_complete, normalize_image, resize_image

__all__ = [
    # From predict.py
    "load_model_and_params",
    "predict_single",
    "predict_batch",
    
    # From model_loader.py
    "load_model",
    "load_norm_params",
    "load_all",
    
    # From data_preprocessing.py
    "preprocess_complete",
    "normalize_image",
    "resize_image",
]

__version__ = "1.0.0"
__author__ = "Goda Emad"
