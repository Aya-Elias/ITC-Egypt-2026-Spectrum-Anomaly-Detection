"""
app.py
------
Entry point - uses st.navigation for instant page switching
"""
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

st.set_page_config(
    page_title="SADAR | Spectrum Anomaly Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ✅ Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ✅ Import all pages
from src.dashboard.pages.home           import show_home
from src.dashboard.pages.realtime       import show_realtime
from src.dashboard.pages.history        import show_history
from src.dashboard.pages.alerts_log     import show_alerts_log
from src.dashboard.pages.analytics      import show_analytics
from src.dashboard.pages.reports        import show_reports
from src.dashboard.pages.live_map       import show_live_map
from src.dashboard.pages.agent_chat     import show_agent_chat
from src.dashboard.pages.system_monitor import show_system_monitor

# ✅ Sidebar
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:16px 4px 14px;">
        <div style="font-size:2.2rem;">🛡️</div>
        <div>
            <div style="font-size:.88rem;font-weight:700;">SADAR</div>
            <div style="font-size:.58rem;color:#00e5ff;font-weight:600;letter-spacing:1.2px;">SPECTRUM ANOMALY DETECTION</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Theme toggle
    if st.button("☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    st.markdown("---")

    # ✅ Navigation buttons
    pages = {
        "🏠 Home":              show_home,
        "📡 Real-time Monitor": show_realtime,
        "📜 History":           show_history,
        "🔔 Alerts Log":        show_alerts_log,
        "📊 Analytics":         show_analytics,
        "📄 Reports":           show_reports,
        "🗺️ Live Map":          show_live_map,
        "🤖 AI Agent":          show_agent_chat,
        "🖥️ System Monitor":    show_system_monitor,
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "🏠 Home"

    for page_name in pages:
        if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
            st.session_state.current_page = page_name

    st.markdown("---")
    st.caption("ITC-EGYPT 2026")

# ✅ Render current page
pages[st.session_state.current_page]()
