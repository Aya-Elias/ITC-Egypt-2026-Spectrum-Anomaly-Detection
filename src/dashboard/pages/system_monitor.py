"""
system_monitor.py
-----------------
System monitor page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import requests
import os
from src.dashboard.data_provider import get_all_data

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1"


def check(url, method="GET", json=None, timeout=1):
    try:
        r = requests.post(url, json=json, timeout=timeout) if method == "POST" else requests.get(url, timeout=timeout)
        if r.ok:
            return ("🟢 Online", r.json(), r.elapsed.total_seconds() * 1000)
        return (f"🔴 Error {r.status_code}", {}, 0)
    except Exception as e:
        return ("🔴 Offline", {"error": str(e)}, 0)


def show_system_monitor():
    """Render the system monitor page."""
    st.caption("Health status of all SADAR system components.")

    if st.button("🔄 Refresh"):
        get_all_data.clear()
        st.rerun()

    st.markdown("### 🖥️ Component Status")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🔵 Spectrum API**")
        status, data, ms = check(f"{API_BASE_URL}/health", timeout=1)
        st.metric("Status", status)
        st.metric("Response Time", f"{ms:.0f} ms")
        if data:
            with st.expander("Details"):
                st.json(data)

    with col2:
        st.markdown("**🤖 AI Agent**")
        status, data, ms = check(f"{API_BASE_URL}/agent/health", timeout=1)
        st.metric("Status", status)
        st.metric("Response Time", f"{ms:.0f} ms")
        if data:
            with st.expander("Details"):
                st.json(data)

    st.markdown("---")
    st.markdown("### 📈 Database Summary")

    # ✅ من cache
    data = get_all_data()

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — statistics unavailable")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("📡 Total Signals", data["total_signals"])
        c2.metric("🚨 Total Alerts",  data["alert_count"])
        c3.metric("🎯 Threshold",     f"{data['threshold']:.0%}")
        if data["label_counts"]:
            st.markdown("### 🏷️ Label Breakdown")
            st.json(data["label_counts"])

    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.info("""
    **SADAR** - Spectrum Anomaly Detection & Response  
    **Version:** 1.0.0  
    **Competition:** ITC-EGYPT 2026  
    **AI Model:** EfficientNet-B0 (93.47% Accuracy)  
    **Agent:** RAG + Ollama  
    **Hardware:** RTL-SDR Compatible  
    """)
