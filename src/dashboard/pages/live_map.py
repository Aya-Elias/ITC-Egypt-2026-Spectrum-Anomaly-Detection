"""
live_map.py
-----------
Live map page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.dashboard.data_provider import get_all_data, get_predictions_filtered


def show_live_map():
    """Render the live map page."""
    st.caption("Geographic distribution of detected spectrum anomalies.")

    data    = get_all_data()
    signals = get_predictions_filtered(limit=200)
    alerts  = data["alerts"]

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — showing cached data")

    anomalies = [s for s in signals if s.get("label") != "Normal"]

    c1, c2, c3 = st.columns(3)
    c1.metric("🚨 Total Alerts",  len(alerts))
    c2.metric("📡 Total Signals", len(signals))
    c3.metric("⚠️ Anomalies",     len(anomalies))

    st.markdown("---")

    if alerts:
        df_alerts = pd.DataFrame(alerts)
        st.markdown("### 📍 Alert Locations")
        cols = [c for c in ["id", "location", "alert_type", "status", "timestamp"] if c in df_alerts.columns]
        st.dataframe(df_alerts[cols], use_container_width=True, hide_index=True)

        if "location" in df_alerts.columns:
            st.markdown("### 🔥 Alert Hotspots")
            hotspots = df_alerts["location"].value_counts().reset_index()
            hotspots.columns = ["Location", "Count"]
            st.bar_chart(hotspots.set_index("Location"))
    else:
        st.info("🟢 No alerts on map — system is clean!")

    if signals:
        df_signals = pd.DataFrame(signals)
        st.markdown("---")

        if "source" in df_signals.columns:
            st.markdown("### 📡 Signal Sources")
            st.bar_chart(df_signals["source"].value_counts())

        if "label" in df_signals.columns:
            st.markdown("### 🏷️ Label Distribution")
            st.bar_chart(df_signals["label"].value_counts())
