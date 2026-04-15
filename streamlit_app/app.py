"""
StrateGPT — Streamlit app entry point.

Run locally:  python -m streamlit run streamlit_app/app.py
Deploy:       point Streamlit Community Cloud at streamlit_app/app.py
"""
import os, sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Allow imports from streamlit_app/ (e.g. core.loader, ui.chat)
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
  /* Dark sidebar */
  section[data-testid="stSidebar"] { background-color: #1D2530 !important; }
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] label { color: #ffffff !important; }
  section[data-testid="stSidebar"] .stMarkdown h1,
  section[data-testid="stSidebar"] .stMarkdown h2,
  section[data-testid="stSidebar"] .stMarkdown h3 { color: #EBCB00 !important; }
  section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }

  /* Source pills */
  .source-pill {
    display: inline-block;
    background: #D4F5EF; color: #1A7A6E;
    border-radius: 20px; padding: 3px 11px;
    font-size: 12px; margin: 2px 3px;
    text-decoration: none; white-space: nowrap;
  }
  .source-pill:hover { background: #aee9df; color: #0f5c53; }

  /* Disclaimer */
  .disclaimer {
    background: #FBF5CC; border: 1px solid #d4a800;
    border-radius: 8px; padding: 7px 16px;
    font-size: 12px; color: #7a5500;
    margin-bottom: 14px;
  }

  /* Tighten chat messages */
  div[data-testid="stChatMessage"] { max-width: 840px; }
</style>
""", unsafe_allow_html=True)

# ── Load resources (cached — runs once per server session) ────────────────────
INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

# ── Session state defaults ────────────────────────────────────────────────────
for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 StrateGPT")
    st.markdown("**U.S. Program Strategy Assistant**")
    st.markdown("*Gates Foundation · Internal*")
    st.divider()

    st.markdown("**Knowledge Base**")
    st.markdown(f"📚 **{len(INDEX)}** strategy documents")
    st.markdown(f"📝 **{len(DOC_TEXTS)}** with extracted text")
    st.caption("K-12 · Postsecondary · Pathways · Data · Charters · Washington State · Amb'45")

    st.divider()

    st.markdown("**Clear conversations**")
    col1, col2, col3 = st.columns(3)
    if col1.button("📚", help="Clear Strategy History", width="stretch"):
        st.session_state["history_msgs"] = []
        st.rerun()
    if col2.button("🔭", help="Clear Ambition 2045", width="stretch"):
        st.session_state["amb45_msgs"] = []
        st.rerun()
    if col3.button("🧠", help="Clear Quiz Me", width="stretch"):
        st.session_state["quiz_msgs"] = []
        st.rerun()

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer">⚠️ Responses generated with AI assistance — '
    'review for accuracy before use. <strong>Internal use only.</strong></div>',
    unsafe_allow_html=True,
)

tab_chat, tab_explorer, tab_synthesis = st.tabs([
    "💬 Chat",
    "📁 Document Explorer",
    "🔀 Strategy Synthesis",
])

with tab_chat:
    mode_history, mode_amb45, mode_quiz = st.tabs([
        "📚 Strategy History",
        "🔭 Ambition 2045",
        "🧠 Quiz Me",
    ])
    with mode_history:
        render_chat("Strategy History", "history_msgs", INDEX, DOC_TEXTS, SKILLS, client)
    with mode_amb45:
        render_chat("Ambition 2045", "amb45_msgs", INDEX, DOC_TEXTS, SKILLS, client)
    with mode_quiz:
        render_chat("Quiz Me", "quiz_msgs", INDEX, DOC_TEXTS, SKILLS, client)

with tab_explorer:
    render_explorer(INDEX, DOC_TEXTS)

with tab_synthesis:
    render_synthesis(INDEX, DOC_TEXTS, SKILLS, client)
