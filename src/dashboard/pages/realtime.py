"""
realtime.py
-----------
Real-time monitoring page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import time
from src.dashboard.data_provider import get_all_data


def show_realtime():
    """Render the real-time monitoring page."""
    auto_refresh = st.toggle("🔄 Auto Refresh (5s)", value=False)

    # ✅ بيانات من cache مشترك
    data = get_all_data(limit=20)

    label_counts = data["label_counts"]
    signals      = data["signals"]
    alerts       = data["alerts"]

    if not data["api_ok"]:
        st.warning("⚠️ API Offline — showing cached data")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛰️ Total Signals", data["total_signals"])
    c2.metric("🚨 Alerts",        data["alert_count"])
    c3.metric("⚠️ Jamming",       label_counts.get("Jamming", 0))
    c4.metric("🚁 Drone",         label_counts.get("Drone", 0))

    st.markdown("---")
    st.markdown("### 🕐 Latest Signals")

    if signals:
        df = pd.DataFrame(signals)

        def color_row(val):
            colors = {
                "Normal":  "background-color:#1a4a1a;color:white",
                "Jamming": "background-color:#4a1a1a;color:white",
                "Drone":   "background-color:#4a3a1a;color:white",
            }
            return colors.get(val, "")

        if "label" in df.columns:
            styled = df.style.applymap(color_row, subset=["label"])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

        if "confidence" in df.columns and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            st.markdown("### 📈 Confidence Trend")
            st.line_chart(df.set_index("timestamp")["confidence"])
    else:
        st.info("⏳ No signals yet — waiting for data...")

    if alerts:
        st.markdown("---")
        st.markdown("### 🚨 Recent Alerts")
        st.dataframe(pd.DataFrame(alerts[:5]), use_container_width=True, hide_index=True)

    if auto_refresh:
        time.sleep(5)
        get_all_data.clear()  # ✅ امسح الـ cache عشان يجيب بيانات جديدة
        st.rerun()
