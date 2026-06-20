"""
alerts_log.py
-------------
Alerts log page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.dashboard.data_provider import get_all_data


def show_alerts_log():
    """Render the alerts log page."""
    st.caption("All triggered anomaly alerts with location and status.")

    data   = get_all_data()
    alerts = data["alerts"]

    if not data["api_ok"]:
        st.warning("⚠️ Cannot reach API — showing cached data")

    if not alerts:
        st.info("🟢 No alerts found — system is clean!")
        return

    df = pd.DataFrame(alerts)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Alerts", len(df))
    c2.metric("Alert Types", df["alert_type"].nunique() if "alert_type" in df.columns else 0)
    c3.metric("Locations",   df["location"].nunique()   if "location"   in df.columns else 0)

    st.markdown("---")

    if "alert_type" in df.columns:
        filter_type = st.selectbox("Filter by Type", ["All"] + df["alert_type"].unique().tolist())
        if filter_type != "All":
            df = df[df["alert_type"] == filter_type]

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button("⬇️ Download CSV", csv, "alerts.csv", "text/csv")

    if "alert_type" in df.columns:
        st.markdown("---")
        st.markdown("### 📊 Alert Distribution")
        st.bar_chart(df["alert_type"].value_counts())
