"""
history.py
----------
Prediction history page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.dashboard.data_provider import get_predictions_filtered, get_all_data


def show_history():
    """Render the prediction history page."""
    st.caption("Browse and filter all past signal predictions.")

    col1, col2 = st.columns(2)
    with col1:
        label_filter = st.selectbox("Filter by Label", ["All", "Normal", "Jamming", "Drone"])
    with col2:
        limit = st.slider("Max Records", 10, 1000, 200)

    # ✅ بيانات من cache
    data    = get_all_data()
    signals = get_predictions_filtered(limit=limit, label=label_filter)

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — showing cached data")

    if not signals:
        st.info("⏳ No predictions found yet.")
        return

    st.caption(f"Showing {len(signals)} records")

    df = pd.DataFrame(signals)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp", ascending=False)

    search = st.text_input("🔍 Search by source, label, or location")
    if search:
        mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button("⬇️ Download CSV", csv, "predictions.csv", "text/csv")
