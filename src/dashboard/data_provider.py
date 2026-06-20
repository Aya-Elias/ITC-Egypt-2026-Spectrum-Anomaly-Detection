"""
data_provider.py
----------------
Centralized cached API data layer for SADAR Dashboard.
Uses parallel fetching for maximum speed.
"""
from __future__ import annotations
import streamlit as st
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1"


def _fetch(url: str) -> dict | list:
    """Single HTTP GET with timeout."""
    try:
        return requests.get(url, timeout=1).json()
    except Exception:
        return {}


@st.cache_data(ttl=5, show_spinner=False)
def get_all_data(limit: int = 20) -> dict:
    """
    Fetch all API data in parallel - single cache hit for all pages.
    Returns a dict with all data needed by every page.
    """
    urls = {
        "statistics":  f"{API_BASE_URL}/statistics",
        "alerts":      f"{API_BASE_URL}/alerts",
        "predictions": f"{API_BASE_URL}/predictions?limit={limit}",
        "health":      f"{API_BASE_URL}/health",
    }

    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {executor.submit(_fetch, url): key for key, url in urls.items()}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = {}

    stats      = results.get("statistics", {})
    alerts_raw = results.get("alerts", [])
    preds_raw  = results.get("predictions", {})
    health_raw = results.get("health", {})

    return {
        "api_ok":        health_raw.get("status") == "ok",
        "total_signals": stats.get("total_signals", 0),
        "alert_count":   stats.get("alert_count", 0),
        "label_counts":  stats.get("label_counts", {}),
        "threshold":     stats.get("alert_threshold", 0.75),
        "alerts":        alerts_raw if isinstance(alerts_raw, list) else [],
        "signals":       preds_raw.get("signals", []) if isinstance(preds_raw, dict) else [],
        "stats":         stats,
    }


@st.cache_data(ttl=5, show_spinner=False)
def get_predictions_filtered(limit: int = 200, label: str = "All") -> list:
    """For history page - filtered predictions."""
    try:
        url = f"{API_BASE_URL}/predictions?limit={limit}"
        if label != "All":
            url += f"&label={label}"
        resp = requests.get(url, timeout=1).json()
        return resp.get("signals", []) if isinstance(resp, dict) else []
    except Exception:
        return []
