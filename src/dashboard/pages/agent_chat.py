"""
agent_chat.py
-------------
AI Agent chat page for the RF Spectrum Anomaly Detection Dashboard.
"""
from __future__ import annotations
import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1"


def show_agent_chat():
    """Render the AI Agent chat page."""
    st.caption("Chat with the SADAR AI Agent about RF signals, threats, and anomalies.")

    # ✅ Check agent health
    ollama_ok = False
    try:
        health    = requests.get(f"{API_BASE_URL}/agent/health", timeout=1).json()
        ollama_ok = health.get("ollama", False)
        if ollama_ok:
            st.success("🟢 AI Agent Online")
        else:
            st.warning("🟡 Agent Online (limited mode)")
    except Exception:
        st.warning("⚠️ Cannot reach API")

    st.markdown("---")

    # ✅ Chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ✅ Input
    if prompt := st.chat_input("Ask about spectrum anomalies, threats, or signal analysis..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("SADAR AI thinking..."):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/agent/ask",
                        json={"question": prompt, "refresh": False, "top_k": 5},
                        timeout=30,
                    )
                    if resp.ok:
                        data    = resp.json()
                        answer  = data.get("answer", str(data))
                        sources = data.get("sources", [])
                        if sources:
                            answer += f"\n\n📚 *Sources: {', '.join(sources[:3])}*"
                    else:
                        answer = f"⚠️ Agent error {resp.status_code}: {resp.text[:200]}"
                except requests.RequestException as exc:
                    answer = f"❌ Cannot reach AI Agent: {exc}"

            st.markdown(answer)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()
