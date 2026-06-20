"""
main.py
-------
Application entry point for the Spectrum Anomaly Detection API.

Startup sequence
----------------
  1. Create FastAPI app instance.
  2. Load the Keras model ONCE → store in app.state.model.
  3. Register middleware (logging, timing, optional API key auth).
  4. Enable CORS.
  5. Mount API routes  (/predict, /predictions, /statistics, /alerts, /health).
  6. Mount WebSocket   (/ws/alerts).

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Environment variables (optional):
    MODEL_PATH   — path to .keras model file (default: best_model.keras)
    MODEL_VER    — model version string shown in responses (default: v1.0)
    API_KEY      — if set, every HTTP request must include X-API-Key header
    ALLOWED_ORIGINS — comma-separated CORS origins (default: *)
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Ensure database package is importable ─────────────────────────
# Adjust this path if your project layout differs.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src/database"))

# ── Internal imports ───────────────────────────────────────────────
from fastapi import APIRouter

try:
    from src.api.routes import router
except Exception as exc:  # database layer is still under construction in this project
    router = APIRouter()
    logger_placeholder_error = exc
else:
    logger_placeholder_error = None

from src.api.agent_routes import router as agent_router
from src.api.websocket import ws_router
from src.api.middleware import LoggingMiddleware
from src.ai_agent import SADARAgent

logger = logging.getLogger("spectrum.main")
if logger_placeholder_error is not None:
    logger.warning("Core prediction routes are unavailable; AI-agent routes remain enabled: %s", logger_placeholder_error)

# ── Configuration from environment ────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "src" / "ai_model" / "saved_models" / "best_model.keras"

MODEL_PATH      = os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH))
MODEL_VERSION   = os.getenv("MODEL_VER", "v1.0")
AI_MODEL_REQUIRED = os.getenv("AI_MODEL_REQUIRED", "0") == "1"
_RAW_ORIGINS    = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _RAW_ORIGINS.split(",")]


# =====================================================================
# LIFESPAN  (replaces deprecated @app.on_event)
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup (before yielding) and once at shutdown (after).

    Startup:
      - Load Keras model from MODEL_PATH.
      - Store model in app.state so every route can access it via
        request.app.state.model without reloading.

    Shutdown:
      - Cleans up model reference (Keras/TF handles GPU/memory itself).
    """
    # ── STARTUP ───────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Spectrum API starting up …")
    logger.info("Model path    : %s", MODEL_PATH)
    logger.info("Model version : %s", MODEL_VERSION)
    logger.info("CORS origins  : %s", ALLOWED_ORIGINS)
    logger.info("=" * 60)

    # The AI-agent endpoints do not require TensorFlow, so initialise them first.
    app.state.sadar_agent = SADARAgent()
    logger.info("SADAR AI Agent initialised.")

    # Import TensorFlow here to avoid slow import at module level and to let
    # /api/v1/agent/* remain available on machines that only run the agent demo.
    app.state.model = None
    app.state.model_version = MODEL_VERSION
    try:
        import tensorflow as tf
        from tensorflow.keras.models import load_model          # type: ignore

        logger.info("TensorFlow version : %s", tf.__version__)

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Keras model not found at '{MODEL_PATH}'. "
                "Set the MODEL_PATH environment variable to the correct path."
            )

        logger.info("Loading model …")
        model = load_model(MODEL_PATH)
        logger.info(
            "Model loaded — input shape: %s | output shape: %s",
            model.input_shape,
            model.output_shape,
        )

        # Warm-up inference so the first real request is not slow.
        import numpy as np
        dummy_shape = tuple(1 if dim is None else int(dim) for dim in model.input_shape)
        dummy = np.zeros(dummy_shape, dtype=np.float32)
        model.predict(dummy, verbose=0)
        logger.info("Warm-up inference complete.")

        app.state.model = model

    except ImportError as exc:
        logger.warning("TensorFlow is not installed; /predict will return 503, agent endpoints remain available.")
        if AI_MODEL_REQUIRED:
            raise exc
    except Exception as exc:
        logger.warning("AI classifier model unavailable; /predict will return 503: %s", exc)
        if AI_MODEL_REQUIRED:
            raise

    logger.info("Spectrum API ready.")
    yield  # ← application runs here

    # ── SHUTDOWN ──────────────────────────────────────────────────
    logger.info("Spectrum API shutting down …")
    app.state.model = None
    logger.info("Model unloaded. Goodbye.")


# =====================================================================
# APP INSTANCE
# =====================================================================

app = FastAPI(
    title="Spectrum Anomaly Detection API",
    description=(
        "Real-time RF signal classification using a deep learning model. "
        "Detects Normal, Jamming, and Drone signals. "
        "Stores predictions in SQLite and broadcasts alerts via WebSocket."
    ),
    version=MODEL_VERSION,
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)


# =====================================================================
# MIDDLEWARE
# =====================================================================

# 1. CORS — must be registered BEFORE LoggingMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request logging + timing + optional API key auth
app.add_middleware(LoggingMiddleware)


# =====================================================================
# ROUTERS
# =====================================================================

# HTTP routes — all prefixed with /api/v1
app.include_router(router, prefix="/api/v1", tags=["API v1"])
app.include_router(agent_router, prefix="/api/v1")

# WebSocket routes — no prefix (connects as ws://host/ws/alerts)
app.include_router(ws_router)


# =====================================================================
# ROOT
# =====================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint — useful for load-balancer health checks.

    Returns:
        {"message": "Spectrum API is running.", "docs": "/docs"}
    """
    return {
        "message": "Spectrum Anomaly Detection API is running.",
        "docs":    "/docs",
        "redoc":   "/redoc",
        "ws":      "ws://host:port/ws/alerts",
    }


# =====================================================================
# DEVELOPMENT ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # ← disable in production
        log_level="info",
    )
