"""
src/api/routes.py
-----------------
FastAPI route handlers for the Spectrum anomaly-detection API.

Endpoints
---------
POST /predict
    Accept signal features → run model inference → save signal →
    maybe create alert → broadcast via WebSocket → return result.

GET  /predictions
    Return all stored signals (paginated, optional label filter).

GET  /statistics
    Return aggregate counts and label distribution.

GET  /alerts
    Return all stored alerts (location decrypted).

GET  /health
    Lightweight liveness check.

Design principles
-----------------
  - Model is read from request.app.state.model (loaded once in main.py).
  - All DB access goes through crud.py — never raw SQL here.
  - Pydantic models validate every input and shape every output.
  - Errors surface as HTTPException with informative messages.
"""

import base64
import io
import time
import logging
from datetime import datetime
from typing import Optional, Any

import numpy as np
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from PIL import Image

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../database"))

from crud import (
    add_signal,
    get_all_signals,
    get_signals_paginated,
    get_signals_filtered,
    get_all_alerts,
    auto_create_alert,
    get_alert_threshold,
    log_action,
)
from .websocket import broadcast_alert

logger = logging.getLogger("spectrum.routes")
router = APIRouter()


# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class SignalInput(BaseModel):
    """
    Input payload for POST /predict.

    Provide exactly one of:
      - spectrogram: nested list shaped (224, 224, 3), values 0-255 or 0-1
      - image_base64: PNG/JPEG spectrogram encoded as base64
      - features: legacy flattened spectrogram vector

    Example request body:
    {
        "features":    [0.12, 0.45, 0.78, ...],   // 1-D feature vector
        "frequency":   433.5,                      // MHz (optional)
        "snr":         15.2,                       // dB  (optional)
        "source":      "SDR-01",                   // sensor ID (optional)
        "alert_type":  "email",                    // email | whatsapp | sound
        "location":    "Sector 7, Cairo"           // where alert is sent
    }
    """
    features:   Optional[list[float]] = Field(None, min_length=1, description="Legacy flattened spectrogram vector")
    spectrogram: Optional[list[Any]]  = Field(None, description="Spectrogram image array shaped 224x224x3")
    image_base64: Optional[str]       = Field(None, description="Base64 encoded spectrogram PNG/JPEG")
    frequency:  Optional[float] = Field(None, ge=0,    description="Detected frequency in MHz")
    snr:        Optional[float] = Field(None,           description="Signal-to-Noise Ratio in dB")
    source:     str             = Field("SDR",          description="Signal source identifier")
    alert_type: str             = Field("email",        description="Alert channel: email | whatsapp | sound")
    location:   str             = Field("Unknown",      description="Threat location description")

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        allowed = {"email", "whatsapp", "sound"}
        if v not in allowed:
            raise ValueError(f"alert_type must be one of {allowed}")
        return v

    @field_validator("image_base64")
    @classmethod
    def strip_data_url(cls, v: Optional[str]) -> Optional[str]:
        if v and "," in v and v.strip().lower().startswith("data:"):
            return v.split(",", 1)[1]
        return v


class PredictionResponse(BaseModel):
    """
    Response payload returned by POST /predict.

    Example:
    {
        "signal_id":        42,
        "label":            "Jamming",
        "confidence":       0.94,
        "inference_time_ms": 312,
        "alert_triggered":  true,
        "alert_id":         7,
        "timestamp":        "2026-04-26T18:00:00.123456",
        "model_version":    "v1.0"
    }
    """
    signal_id:          int
    label:              str
    confidence:         float
    inference_time_ms:  int
    alert_triggered:    bool
    alert_id:           Optional[int]
    timestamp:          str
    model_version:      str


class PaginatedSignals(BaseModel):
    total:   int
    page:    int
    limit:   int
    signals: list[dict]


class StatisticsResponse(BaseModel):
    total_signals:  int
    label_counts:   dict[str, int]
    alert_count:    int
    alert_threshold: float


# =====================================================================
# INFERENCE HELPER
# =====================================================================

# Labels must match the model's output class order
LABEL_MAP: dict[int, str] = {
    0: "Drone",
    1: "Normal",
    2: "Jamming",
}

def _prepare_model_input(payload: SignalInput, model) -> np.ndarray:
    """Convert API payload into the Keras model input shape.

    The trained EfficientNet model expects spectrogram images shaped
    (batch, 224, 224, 3). Values are normalized to [0, 1].
    """
    provided = [payload.features is not None, payload.spectrogram is not None, payload.image_base64 is not None]
    if sum(provided) != 1:
        raise ValueError("Provide exactly one of: features, spectrogram, image_base64")

    if payload.image_base64 is not None:
        raw = base64.b64decode(payload.image_base64)
        image = Image.open(io.BytesIO(raw)).convert("RGB").resize((224, 224))
        arr = np.asarray(image, dtype=np.float32)
    elif payload.spectrogram is not None:
        arr = np.asarray(payload.spectrogram, dtype=np.float32)
    else:
        arr = np.asarray(payload.features, dtype=np.float32)

    expected_shape = tuple(1 if dim is None else int(dim) for dim in getattr(model, "input_shape", (None, 224, 224, 3)))
    expected_no_batch = expected_shape[1:]

    if arr.ndim == 1:
        if int(np.prod(expected_no_batch)) != arr.size:
            raise ValueError(f"Flattened features length {arr.size} does not match expected {expected_no_batch}")
        arr = arr.reshape(expected_no_batch)

    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)

    if arr.shape[:2] != expected_no_batch[:2]:
        image = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
        image = image.resize((expected_no_batch[1], expected_no_batch[0]))
        arr = np.asarray(image, dtype=np.float32)

    if arr.shape != expected_no_batch:
        raise ValueError(f"Prepared input shape {arr.shape} does not match model input {expected_no_batch}")

    if arr.max(initial=0) > 1.0:
        arr = arr / 255.0
    return np.expand_dims(arr.astype(np.float32), axis=0)


def _run_inference(model, payload: SignalInput) -> tuple[str, float, int]:
    """
    Feeds the feature vector to the Keras model and returns
    (class_label, confidence_score, inference_time_ms).

    The model expects shape (1, N) where N == len(features).
    Adjust the reshape if your model expects a 2-D spectrogram.
    """
    x = _prepare_model_input(payload, model)

    start = time.perf_counter()
    raw_output = model.predict(x, verbose=0)                   # shape (1, num_classes)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # raw_output shape: (1, num_classes) → take the first row
    probs = raw_output[0]
    class_idx = int(np.argmax(probs))
    confidence = float(probs[class_idx])
    label = LABEL_MAP.get(class_idx, f"class_{class_idx}")

    return label, confidence, elapsed_ms


# =====================================================================
# ROUTES
# =====================================================================

@router.get("/health", tags=["System"])
async def health_check():
    """
    Liveness probe — returns 200 if the API is running.

    Example response:
        {"status": "ok", "timestamp": "2026-04-26T18:00:00"}
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ------------------------------------------------------------------
# POST /predict
# ------------------------------------------------------------------
@router.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Inference"],
    summary="Run model inference on a signal feature vector",
)
async def predict(payload: SignalInput, request: Request):
    """
    Full prediction pipeline:

      1. Validate input (Pydantic).
      2. Pull Keras model from app.state (loaded once at startup).
      3. Run inference → label + confidence.
      4. Persist signal via crud.add_signal().
      5. Auto-create alert (respects threshold + whitelist logic).
      6. Broadcast alert over WebSocket if triggered.
      7. Log action to audit_logs.
      8. Return PredictionResponse.

    Example request:
        POST /predict
        {
            "features": [0.12, 0.45, 0.78, 0.33, 0.91],
            "frequency": 433.5,
            "snr": 15.2,
            "source": "SDR-01",
            "alert_type": "email",
            "location": "Sector 7, Cairo"
        }

    Example response (anomaly detected):
        {
            "signal_id": 42,
            "label": "Jamming",
            "confidence": 0.94,
            "inference_time_ms": 312,
            "alert_triggered": true,
            "alert_id": 7,
            "timestamp": "2026-04-26T18:00:00.123456",
            "model_version": "v1.0"
        }
    """
    # ── Step 1: Retrieve model (never reload — loaded once in main.py) ──
    model = getattr(request.app.state, "model", None)
    if model is None:
        logger.error("Model not loaded — app.state.model is None")
        raise HTTPException(status_code=503, detail="AI model is not available.")

    model_version: str = getattr(request.app.state, "model_version", "unknown")

    # ── Step 2: Run inference ──────────────────────────────────────
    try:
        label, confidence, inference_time_ms = _run_inference(model, payload)
    except Exception as exc:
        logger.exception("Inference failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Model inference error: {exc}")

    logger.info(
        "Inference — label=%s | confidence=%.4f | time=%dms",
        label, confidence, inference_time_ms,
    )

    # ── Step 3: Persist signal ─────────────────────────────────────
    signal_id = add_signal(
        label=label,
        confidence=confidence,
        frequency=payload.frequency,
        snr=payload.snr,
        source=payload.source,
        inference_time_ms=inference_time_ms,
        model_version=model_version,
    )
    if signal_id is None:
        raise HTTPException(status_code=500, detail="Failed to save signal to database.")

    # ── Step 4: Auto-create alert (threshold + whitelist check) ───
    alert_id: Optional[int] = None
    alert_triggered = False

    if label != "Normal":
        alert_id = auto_create_alert(
            signal_id=signal_id,
            alert_type=payload.alert_type,
            location=payload.location,
        )
        alert_triggered = alert_id is not None

    # ── Step 5: Broadcast over WebSocket if alert was created ──────
    if alert_triggered:
        await broadcast_alert({
            "alert_id":   alert_id,
            "signal_id":  signal_id,
            "label":      label,
            "confidence": round(confidence, 4),
            "alert_type": payload.alert_type,
            "location":   payload.location,
            "timestamp":  datetime.now().isoformat(),
        })

    # ── Step 6: Audit log ──────────────────────────────────────────
    log_action(
        action="PREDICT",
        details=(
            f"signal_id={signal_id} label={label} "
            f"confidence={confidence:.4f} alert={alert_triggered}"
        ),
    )

    # ── Step 7: Return result ──────────────────────────────────────
    return PredictionResponse(
        signal_id=signal_id,
        label=label,
        confidence=round(confidence, 4),
        inference_time_ms=inference_time_ms,
        alert_triggered=alert_triggered,
        alert_id=alert_id,
        timestamp=datetime.now().isoformat(),
        model_version=model_version,
    )


# ------------------------------------------------------------------
# GET /predictions
# ------------------------------------------------------------------
@router.get(
    "/predictions",
    response_model=PaginatedSignals,
    tags=["Signals"],
    summary="Retrieve stored signals with optional filtering and pagination",
)
async def get_predictions(
    label:  Optional[str] = Query(None, description="Filter by label: Normal | Jamming | Drone"),
    limit:  int           = Query(100,  ge=1, le=1000, description="Max rows per page"),
    offset: int           = Query(0,    ge=0,          description="Rows to skip (pagination)"),
):
    """
    Returns paginated signals from the database.

    Query params:
      - label:  optional filter (Normal / Jamming / Drone)
      - limit:  rows per page (default 100, max 1000)
      - offset: skip N rows (for paging)

    Example:
        GET /predictions?label=Jamming&limit=50&offset=0
    """
    if label:
        signals = get_signals_filtered(label=label, limit=limit)
    else:
        signals = get_signals_paginated(limit=limit, offset=offset)

    return PaginatedSignals(
        total=len(signals),
        page=(offset // limit) + 1,
        limit=limit,
        signals=signals,
    )


# ------------------------------------------------------------------
# GET /statistics
# ------------------------------------------------------------------
@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    tags=["Analytics"],
    summary="Aggregate statistics: signal counts, label distribution, alert count",
)
async def get_statistics():
    """
    Returns a high-level summary built from the database.

    Example response:
        {
            "total_signals": 1024,
            "label_counts": {"Normal": 900, "Jamming": 80, "Drone": 44},
            "alert_count": 124,
            "alert_threshold": 0.75
        }
    """
    all_signals = get_all_signals()
    all_alerts  = get_all_alerts(decrypt_fields=False)  # faster — no decryption needed
    threshold   = get_alert_threshold()

    label_counts: dict[str, int] = {}
    for sig in all_signals:
        lbl = sig.get("label", "Unknown")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    return StatisticsResponse(
        total_signals=len(all_signals),
        label_counts=label_counts,
        alert_count=len(all_alerts),
        alert_threshold=threshold,
    )


# ------------------------------------------------------------------
# GET /alerts
# ------------------------------------------------------------------
@router.get(
    "/alerts",
    tags=["Alerts"],
    summary="Retrieve all stored alerts with decrypted location",
)
async def get_alerts():
    """
    Returns all alerts. The encrypted location field is automatically
    decrypted before returning (handled inside crud.get_all_alerts).

    Example response item:
        {
            "id": 7,
            "signal_id": 42,
            "timestamp": "2026-04-26T18:00:00",
            "alert_type": "email",
            "status": "sent",
            "location": "Sector 7, Cairo"
        }
    """
    return get_all_alerts(decrypt_fields=True)
