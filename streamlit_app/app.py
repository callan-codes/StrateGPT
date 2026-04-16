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

from core.loader   import load_all, get_client
from ui.overview   import render_overview
from ui.chat       import render_chat
from ui.explorer   import render_explorer
from ui.synthesis  import render_synthesis

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StrateGPT — USP Strategy Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS (adapted from research-discovery.replit.app) ──────────────────
st.markdown("""
<style>
  /* ── Color tokens ── */
  :root {
    --navy:     #0A2240;
    --teal:     #0B9E80;
    --teal-br:  #3DDBB0;
    --blue:     #1A6BC4;
    --purple:   #5E52D4;
    --tl:       #D6F5EC;
    --bl:       #DFF0FF;
    --pl:       #EEECFF;
    --text:     #0D1B2A;
    --muted:    #596577;
    --border:   #D8E3F0;
    --surf:     #F2F7FD;
    --white:    #ffffff;
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; }

  /* ── Top nav banner ── */
  .topnav {
    background: var(--navy);
    border-bottom: 2px solid var(--teal-br);
    height: 48px;
    display: flex; align-items: center; gap: 10px;
    padding: 0 24px;
    margin: -1rem -1rem 1.5rem -1rem;
    position: sticky; top: 0; z-index: 999;
  }
  .topnav-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--teal-br); flex-shrink: 0;
  }
  .topnav-brand {
    font-family: Georgia, serif; font-size: 16px;
    color: #fff; font-weight: normal; letter-spacing: 0.2px;
  }
  .topnav-sub {
    font-size: 12px; color: rgba(255,255,255,0.45);
  }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background-color: #1E3D5C !important;
    border-right: none !important;
  }
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] caption { color: rgba(255,255,255,0.88) !important; }
  section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12); }

  /* Sidebar brand */
  .sb-brand {
    font-family: Georgia, serif; font-size: 16px;
    color: #fff; font-weight: normal; margin-bottom: 2px;
  }
  .sb-sub {
    font-size: 11px; color: rgba(255,255,255,0.45); margin-bottom: 0;
  }

  /* Sidebar group label */
  .sb-grp {
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,0.4); font-weight: 700;
    padding: 14px 0 6px 2px;
  }

  /* Nav radio — styled as menu items */
  section[data-testid="stSidebar"] .stRadio > label { display: none; }
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 2px; }
  section[data-testid="stSidebar"] .stRadio label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 9px 10px !important;
    font-size: 12px !important;
    font-family: Georgia, serif;
    color: rgba(255,255,255,0.75) !important;
    width: 100%;
    transition: background 0.15s;
    border-left: 3px solid transparent !important;
  }
  section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.10) !important;
  }
  section[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: rgba(255,255,255,0.16) !important;
    border-left-color: var(--teal-br) !important;
    color: var(--teal-br) !important;
    font-weight: 600;
  }
  /* Inject "SENSEMAKING TOOLS" group label before 2nd nav item via CSS */
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:nth-child(2) {
    margin-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.10);
    padding-top: 14px !important;
  }
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:nth-child(2)::before {
    content: "SENSEMAKING TOOLS";
    display: block;
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,0.4); font-family: 'Segoe UI', system-ui, sans-serif;
    font-weight: 700; margin-bottom: 8px;
  }

  /* ── Tool header ── */
  .t-hdr {
    padding: 24px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }
  .t-ey {
    font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--teal); font-weight: 700; margin-bottom: 6px;
  }
  .t-title {
    font-family: Georgia, serif; font-size: 26px;
    color: var(--navy); line-height: 1.2; margin-bottom: 8px;
  }
  .t-tag {
    font-size: 15px; color: var(--muted);
    font-style: italic; max-width: 640px; line-height: 1.5;
  }

  /* ── Cards ── */
  .card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
  }
  .card-ey {
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); font-weight: 700; margin-bottom: 4px;
  }
  .card-title {
    font-family: Georgia, serif; font-size: 15px;
    color: var(--navy); margin-bottom: 8px;
  }
  .card-body { font-size: 14px; color: var(--muted); line-height: 1.6; }

  /* ── Tool cards (overview) ── */
  .tool-card {
    background: var(--white); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px 18px;
    height: 100%;
  }
  .tool-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
  .tool-icon {
    width: 40px; height: 40px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; margin-bottom: 12px;
  }
  .tool-name {
    font-family: Georgia, serif; font-size: 14px;
    color: var(--navy); font-weight: normal; margin-bottom: 6px;
  }
  .tool-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }

  /* ── Chips ── */
  .chip {
    display: inline-block; font-size: 11px;
    padding: 4px 10px; border-radius: 14px;
  }
  .chip-teal   { background: var(--tl); color: #0D5F40; }
  .chip-blue   { background: var(--bl); color: #0D4A8A; }
  .chip-purple { background: var(--pl); color: #3D2EA0; }
  .chip-navy   { background: #E8EFF8; color: var(--navy); }

  /* ── Source pills ── */
  .source-pill {
    display: inline-block;
    background: var(--tl); color: #0D5F40;
    border-radius: 20px; padding: 3px 11px;
    font-size: 12px; margin: 2px 3px;
    text-decoration: none; white-space: nowrap;
  }
  .source-pill:hover { background: #b2ead8; }

  /* ── Disclaimer ── */
  .disclaimer {
    background: #FEF3D7; border: 1px solid #D4921A;
    border-radius: 8px; padding: 7px 16px;
    font-size: 12px; color: #7A4A00;
    margin-bottom: 20px;
  }

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
    st.markdown('<div class="sb-brand">🤖 StrateGPT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-sub">Gates Foundation · Internal</div>', unsafe_allow_html=True)
    st.divider()

    section = st.radio(
        "Navigation",
        options=[
            "🏠  Overview",
            "💬  StrateGPT Chat",
            "📁  Document Explorer",
            "🔀  Strategy Synthesizer",
        ],
        label_visibility="collapsed",
    )

# ── Top banner ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="topnav-dot"></div>
  <span class="topnav-brand">StrateGPT</span>
  <span class="topnav-sub">U.S. Program Strategy Assistant &nbsp;·&nbsp; Gates Foundation Internal</span>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="disclaimer">⚠️ Responses generated with AI assistance — '
    'review for accuracy before use. <strong>Internal use only.</strong></div>',
    unsafe_allow_html=True,
)

# ── Main content — driven by sidebar nav ─────────────────────────────────────
if section == "🏠  Overview":
    render_overview()

elif section == "💬  StrateGPT Chat":
    st.markdown('<div class="t-hdr"><div class="t-ey">SENSEMAKING TOOLS</div>'
                '<div class="t-title">StrateGPT Chat</div>'
                '<div class="t-tag">Ask questions across strategy history, Ambition 2045, '
                'or test your knowledge.</div></div>', unsafe_allow_html=True)

    tab_history, tab_amb45, tab_quiz = st.tabs([
        "📚 Strategy History",
        "🔭 Ambition 2045",
        "🧠 Quiz Me",
    ])
    with tab_history:
        render_chat("Strategy History", "history_msgs", INDEX, DOC_TEXTS, SKILLS, client)
    with tab_amb45:
        render_chat("Ambition 2045",    "amb45_msgs",   INDEX, DOC_TEXTS, SKILLS, client)
    with tab_quiz:
        render_chat("Quiz Me",          "quiz_msgs",    INDEX, DOC_TEXTS, SKILLS, client)

elif section == "📁  Document Explorer":
    st.markdown('<div class="t-hdr"><div class="t-ey">SENSEMAKING TOOLS</div>'
                '<div class="t-title">Document Explorer</div>'
                '<div class="t-tag">Browse, filter, and search all 584 indexed '
                'strategy documents.</div></div>', unsafe_allow_html=True)
    render_explorer(INDEX, DOC_TEXTS)

elif section == "🔀  Strategy Synthesizer":
    st.markdown('<div class="t-hdr"><div class="t-ey">SENSEMAKING TOOLS</div>'
                '<div class="t-title">Strategy Synthesizer</div>'
                '<div class="t-tag">Ask cross-cutting questions across multiple strategy '
                'areas and surface shared themes and tensions.</div></div>',
                unsafe_allow_html=True)
    render_synthesis(INDEX, DOC_TEXTS, SKILLS, client)
