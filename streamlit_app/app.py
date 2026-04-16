"""
StrateGPT V2 — Streamlit app entry point.

Run locally:  python -m streamlit run streamlit_app/app.py
Deploy:       point Streamlit Community Cloud at streamlit_app/app.py
"""
import os, sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.loader import load_all, get_client
from ui.chat      import render_chat
from ui.explorer  import render_explorer
from ui.synthesis import render_synthesis

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StrateGPT — USP Strategy Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Sidebar ── */
  section[data-testid="stSidebar"] { background-color: #1D2530 !important; }
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] label { color: #ffffff !important; }
  section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }

  /* Nav radio — make it look like a menu */
  section[data-testid="stSidebar"] .stRadio > label { display: none; }
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px; }
  section[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.07);
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-weight: 500;
    width: 100%;
    transition: background 0.15s;
  }
  section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.14) !important;
  }
  section[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: #EBCB00 !important;
    color: #1D2530 !important;
  }

  /* ── Top banner ── */
  .sgpt-banner {
    background: #1D2530;
    border-radius: 10px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 18px;
  }
  .sgpt-banner-icon {
    background: #248af9;
    width: 46px; height: 46px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0;
  }
  .sgpt-banner-title {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
    line-height: 1.2;
  }
  .sgpt-banner-subtitle {
    color: rgba(255,255,255,0.6);
    font-size: 13px;
    margin-top: 2px;
  }

  /* ── Disclaimer ── */
  .disclaimer {
    background: #FBF5CC; border: 1px solid #d4a800;
    border-radius: 8px; padding: 7px 16px;
    font-size: 12px; color: #7a5500;
    margin-bottom: 16px;
  }

  /* ── Source pills ── */
  .source-pill {
    display: inline-block;
    background: #D4F5EF; color: #1A7A6E;
    border-radius: 20px; padding: 3px 11px;
    font-size: 12px; margin: 2px 3px;
    text-decoration: none; white-space: nowrap;
  }
  .source-pill:hover { background: #aee9df; color: #0f5c53; }

  /* ── Chat messages ── */
  div[data-testid="stChatMessage"] { max-width: 840px; }
</style>
""", unsafe_allow_html=True)

# ── Load resources ────────────────────────────────────────────────────────────
INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

# ── Session state ─────────────────────────────────────────────────────────────
for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 StrateGPT")
    st.caption("Gates Foundation · Internal")
    st.divider()

    section = st.radio(
        "Navigation",
        options=["💬  Chat", "📁  Document Explorer", "🔀  Strategy Synthesis"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Knowledge Base**")
    st.markdown(f"📚 **{len(INDEX)}** strategy documents")
    st.markdown(f"📝 **{len(DOC_TEXTS)}** with extracted text")
    st.caption("K-12 · Postsecondary · Pathways\nData · Charters · Wash. State · Amb'45")

    if section == "💬  Chat":
        st.divider()
        st.markdown("**Clear history**")
        c1, c2, c3 = st.columns(3)
        if c1.button("📚", help="Clear Strategy History"):
            st.session_state["history_msgs"] = []
            st.rerun()
        if c2.button("🔭", help="Clear Ambition 2045"):
            st.session_state["amb45_msgs"] = []
            st.rerun()
        if c3.button("🧠", help="Clear Quiz Me"):
            st.session_state["quiz_msgs"] = []
            st.rerun()

# ── Banner ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sgpt-banner">
  <div class="sgpt-banner-icon">🤖</div>
  <div>
    <div class="sgpt-banner-title">StrateGPT</div>
    <div class="sgpt-banner-subtitle">U.S. Program Strategy Assistant</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="disclaimer">⚠️ Responses generated with AI assistance — '
    'review for accuracy before use. <strong>Internal use only.</strong></div>',
    unsafe_allow_html=True,
)

# ── Main content — driven by sidebar nav ─────────────────────────────────────
if section == "💬  Chat":
    tab_history, tab_amb45, tab_quiz = st.tabs([
        "📚 Strategy History",
        "🔭 Ambition 2045",
        "🧠 Quiz Me",
    ])
    with tab_history:
        render_chat("Strategy History", "history_msgs", INDEX, DOC_TEXTS, SKILLS, client)
    with tab_amb45:
        render_chat("Ambition 2045", "amb45_msgs", INDEX, DOC_TEXTS, SKILLS, client)
    with tab_quiz:
        render_chat("Quiz Me", "quiz_msgs", INDEX, DOC_TEXTS, SKILLS, client)

elif section == "📁  Document Explorer":
    render_explorer(INDEX, DOC_TEXTS)

elif section == "🔀  Strategy Synthesis":
    render_synthesis(INDEX, DOC_TEXTS, SKILLS, client)
