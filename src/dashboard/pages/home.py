"""
home.py
-------
Home page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.dashboard.data_provider import get_all_data


def show_home():
    """Render the home page."""

    # ✅ بيانات من cache مشترك - مش بيعمل API calls جديدة
    data = get_all_data(limit=5)

    api_ok        = data["api_ok"]
    total_signals = data["total_signals"]
    total_alerts  = data["alert_count"]
    label_counts  = data["label_counts"]
    alerts        = data["alerts"]
    signals       = data["signals"]
    anomalies     = sum(v for k, v in label_counts.items() if k != "Normal")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛰️ API Status",    "🟢 Online" if api_ok else "🔴 Offline")
    c2.metric("📡 Total Signals", total_signals)
    c3.metric("🚨 Total Alerts",  total_alerts)
    c4.metric("⚠️ Anomalies",     anomalies)

    st.markdown("---")

    # --- Quick Actions ---
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📡 Start Monitoring", use_container_width=True):
            st.session_state.current_page = "📡 Real-time Monitor"; st.rerun()
    with col2:
        if st.button("📜 View History", use_container_width=True):
            st.session_state.current_page = "📜 History"; st.rerun()
    with col3:
        if st.button("🤖 AI Agent", use_container_width=True):
            st.session_state.current_page = "🤖 AI Agent"; st.rerun()
    with col4:
        if st.button("🔔 Alerts Log", use_container_width=True):
            st.session_state.current_page = "🔔 Alerts Log"; st.rerun()

    st.markdown("---")

    # --- Recent Signals & Alerts ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📡 Recent Signals")
        if signals:
            for s in signals[:5]:
                label      = s.get("label", "Unknown")
                confidence = s.get("confidence", 0)
                ts         = s.get("timestamp", "")[:19]
                color = {"Normal": "#00c851", "Jamming": "#ff4444", "Drone": "#ff8800"}.get(label, "gray")
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                    f"border-bottom:1px solid #333;'>"
                    f"<span style='color:{color};font-weight:600;'>{label}</span>"
                    f"<span>{confidence:.1%}</span>"
                    f"<span style='color:gray;font-size:0.8rem;'>{ts}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No signals yet")

    with col2:
        st.markdown("### 🚨 Recent Alerts")
        if alerts:
            for a in alerts[:5]:
                alert_type = a.get("alert_type", "Unknown")
                location   = a.get("location", "Unknown")
                ts         = a.get("timestamp", "")[:19]
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                    f"border-bottom:1px solid #333;'>"
                    f"<span style='color:#ff4444;font-weight:600;'>🚨 {alert_type}</span>"
                    f"<span style='font-size:0.8rem;'>{location}</span>"
                    f"<span style='color:gray;font-size:0.8rem;'>{ts}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("🟢 No alerts — system clean")

    st.markdown("---")

    # --- System Components ---
    st.markdown("### 🖥️ System Components")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🤖 AI Model**\nEfficientNet-B0\n93.47% Accuracy")
    with col2:
        st.info("**🧠 AI Agent**\nRAG + Ollama\nArabic/English")
    with col3:
        st.info("**📡 Hardware**\nRTL-SDR Compatible\n2.4 / 5.8 GHz")

    # --- Label Distribution ---
    if label_counts:
        st.markdown("---")
        st.markdown("### 📊 Label Distribution")
        df = pd.DataFrame(list(label_counts.items()), columns=["Label", "Count"]).set_index("Label")
        st.bar_chart(df)
