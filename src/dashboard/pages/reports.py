"""
reports.py
----------
Reports page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import requests
import os
from src.dashboard.data_provider import get_all_data

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1"


def show_reports():
    """Render the reports page."""
    st.caption("Generate AI-powered threat analysis reports.")
    st.markdown("### 🔍 Threat Analysis Report")

    with st.form("report_form"):
        col1, col2 = st.columns(2)
        with col1:
            label     = st.selectbox("Signal Label", ["Drone", "Jamming", "Normal"])
            frequency = st.number_input("Frequency (MHz)", min_value=0.0, value=433.5)
        with col2:
            confidence = st.slider("Confidence", 0.0, 1.0, 0.85)
            snr        = st.number_input("SNR (dB)", value=15.0)
        location      = st.text_input("Location", value="Cairo, Egypt")
        analyst_notes = st.text_area("Analyst Notes (optional)", height=80)
        submitted     = st.form_submit_button("🤖 Generate Report", type="primary")

    if submitted:
        with st.spinner("Generating AI threat analysis report..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/agent/report",
                    json={
                        "label":         label,
                        "confidence":    confidence,
                        "frequency_mhz": frequency,
                        "snr_db":        snr,
                        "location":      location,
                        "analyst_notes": analyst_notes,
                    },
                    timeout=30,
                )
                if resp.ok:
                    report = resp.json().get("markdown", str(resp.json()))
                    st.success("✅ Report Generated")
                    st.markdown("---")
                    st.markdown(report)
                    st.download_button("⬇️ Download Report", report, "sadar_report.md", "text/markdown")
                else:
                    st.error(f"API error {resp.status_code}: {resp.text[:300]}")
            except requests.RequestException as exc:
                st.error(f"❌ Cannot reach AI Agent: {exc}")

    st.markdown("---")
    st.markdown("### 📊 Quick Statistics")

    # ✅ من cache
    data = get_all_data()

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — statistics unavailable")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Signals", data["total_signals"])
        c2.metric("Total Alerts",  data["alert_count"])
        c3.metric("Threshold",     f"{data['threshold']:.0%}")
        if data["label_counts"]:
            st.json(data["label_counts"])
