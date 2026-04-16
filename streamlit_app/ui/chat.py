"""
chat.py — Chat tab UI.

Handles all three modes: Strategy History, Ambition 2045, Quiz Me.
Responses stream word-by-word. Sources appear in a collapsible expander.
"""
import streamlit as st
from core.retrieval import retrieve
from core.prompts   import build_system, stream_response
from core.loader    import to_url

# Map display mode name → backend mode string
BACKEND_MODE = {
    "Strategy History": "history",
    "Ambition 2045":    "amb45",
    "Quiz Me":          "quiz",
}

PLACEHOLDERS = {
    "Strategy History": "e.g. How has the Postsecondary Success strategy evolved since 2019?",
    "Ambition 2045":    "e.g. How does Amb'45 build on prior Postsecondary work?",
    "Quiz Me":          "Type a topic to quiz on, or just type 'start'…",
}

MODE_DESCRIPTIONS = {
    "Strategy History": "Ask any question about U.S. Program strategies from 2019 to present.",
    "Ambition 2045":    "Explore how Ambition 2045 connects to — and departs from — historical USP strategy.",
    "Quiz Me":          "Test your knowledge. Type a topic or just say 'start' for a random question.",
}

DOC_ICONS = {
    "memo": "📄", "cover-note": "📄", "email": "📧",
    "presentation": "📊", "investment-scoring": "📊",
    "meeting-notes": "📝", "follow-ups": "📝",
    "investment-narrative": "📋", "investment-plan": "📋",
    "pre-read": "📖", "digital-binder": "📁",
    "placemat": "📌", "video": "🎥",
}


def render_source_pills(docs: list):
    """Render retrieved documents as teal pills, linked if URL is available."""
    pills = []
    for d in docs:
        icon  = DOC_ICONS.get(d["doc_type"], "📄")
        label = (d["meeting_topic"] or d["filename"])
        label = label[:48] + "…" if len(label) > 48 else label
        year  = f" ({d['session_year']})" if d["session_year"] else ""
        url   = to_url(d["path"])
        if url.startswith("file"):
            pills.append(f'<span class="source-pill">{icon} {label}{year}</span>')
        else:
            pills.append(f'<a class="source-pill" href="{url}" target="_blank">{icon} {label}{year}</a>')
    st.markdown(" ".join(pills), unsafe_allow_html=True)


def render_chat(mode_name: str, session_key: str,
                index: list, doc_texts: dict, skills: str, client):
    """Render the full Chat tab for the given mode."""

    backend_mode = BACKEND_MODE[mode_name]
    history      = st.session_state[session_key]

    st.caption(MODE_DESCRIPTIONS[mode_name])

    # ── Render conversation history ───────────────────────────────────────────
    for msg in history:
        role   = "user" if msg["role"] == "user" else "assistant"
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"📎 {len(msg['sources'])} source(s) retrieved"):
                    render_source_pills(msg["sources"])

    # ── Input ─────────────────────────────────────────────────────────────────
    prompt = st.chat_input(PLACEHOLDERS[mode_name])

    if prompt:
        # Add user message
        st.session_state[session_key].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Retrieve and stream
        docs   = retrieve(prompt, backend_mode, index, doc_texts)
        system = build_system(backend_mode, docs, doc_texts, skills)

        with st.chat_message("assistant", avatar="🤖"):
            full_response = st.write_stream(
                stream_response(client, system, history, prompt)
            )
            if docs:
                with st.expander(f"📎 {len(docs)} source(s) retrieved"):
                    render_source_pills(docs)

        # Persist AI message
        st.session_state[session_key].append({
            "role":    "ai",
            "content": full_response,
            "sources": docs,
        })
