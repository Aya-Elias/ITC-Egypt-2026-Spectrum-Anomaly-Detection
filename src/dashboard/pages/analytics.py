"""
analytics.py
------------
Analytics page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.dashboard.data_provider import get_all_data, get_predictions_filtered


def show_analytics():
    """Render the analytics page."""
    st.caption("Signal statistics, label distribution, and anomaly trends.")

    # ✅ بيانات من cache مشترك
    data    = get_all_data()
    signals = get_predictions_filtered(limit=500)

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — showing cached data")

    label_counts  = data["label_counts"]
    total_signals = data["total_signals"]
    total_alerts  = data["alert_count"]
    threshold     = data["threshold"]
    anomalies     = sum(v for k, v in label_counts.items() if k != "Normal")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📡 Total Signals",   total_signals)
    c2.metric("🚨 Total Alerts",    total_alerts)
    c3.metric("⚠️ Anomalies",       anomalies)
    c4.metric("🎯 Alert Threshold", f"{threshold:.0%}")

    st.markdown("---")

    if label_counts:
        st.markdown("### 📊 Label Distribution")
        col1, col2 = st.columns(2)
        df_labels = pd.DataFrame(list(label_counts.items()), columns=["Label", "Count"]).set_index("Label")
        with col1:
            st.bar_chart(df_labels)
        with col2:
            st.dataframe(df_labels, use_container_width=True)

    if signals:
        df = pd.DataFrame(signals)
        st.markdown("---")

        if "confidence" in df.columns and "timestamp" in df.columns:
            st.markdown("### 📈 Confidence Over Time")
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            st.line_chart(df.set_index("timestamp")["confidence"])

        if "source" in df.columns:
            st.markdown("---")
            st.markdown("### 📡 Signal Sources")
            st.bar_chart(df["source"].value_counts())

        st.markdown("---")
        st.markdown("### 🗂️ Recent Signals")
        st.dataframe(df.tail(50), use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", csv, "signals.csv", "text/csv")
    else:
        st.info("⏳ No signal data yet.")
