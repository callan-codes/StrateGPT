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
    page_title="StrateGPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Hide Streamlit chrome + sidebar ── */
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="collapsedControl"] { display: none !important; }
  section[data-testid="stSidebar"]  { display: none !important; }
  .block-container { padding: 0 !important; max-width: 100% !important; }

  /* ── Color tokens ── */
  :root {
    --navy:    #0A2240;
    --sidebar: #1E3D5C;
    --teal:    #0B9E80;
    --teal-br: #3DDBB0;
    --blue:    #1A6BC4;
    --purple:  #5E52D4;
    --tl:      #D6F5EC;
    --bl:      #DFF0FF;
    --pl:      #EEECFF;
    --text:    #0D1B2A;
    --muted:   #596577;
    --border:  #D8E3F0;
    --surf:    #F2F7FD;
    --white:   #ffffff;
  }

  /* ── Top banner ── */
  .topnav {
    background: var(--navy);
    border-bottom: 2px solid var(--teal-br);
    height: 52px;
    display: flex; align-items: center; gap: 12px;
    padding: 0 28px;
    margin: 0;
  }
  .topnav-dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--teal-br); flex-shrink: 0;
  }
  .topnav-brand {
    font-family: Georgia, serif; font-size: 17px;
    color: #fff; font-weight: normal; letter-spacing: 0.2px;
  }
  .topnav-div { color: rgba(255,255,255,0.25); font-size: 14px; }
  .topnav-sub { font-size: 12px; color: rgba(255,255,255,0.45); }

  /* ── Nav column (left panel) ── */
  div[data-testid="stColumn"]:first-child > div:first-child {
    background-color: var(--sidebar);
    border-radius: 0;
    min-height: 100vh;
    padding: 20px 12px !important;
  }

  /* Reset nested columns — don't inherit nav panel styling */
  div[data-testid="stColumn"] div[data-testid="stColumn"]:first-child > div:first-child {
    background-color: transparent !important;
    border-radius: 0 !important;
    min-height: unset !important;
    padding: 0 !important;
  }

  /* Nav tile buttons */
  div[data-testid="stColumn"]:first-child .stButton button {
    background: transparent !important;
    color: rgba(255,255,255,0.72) !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 8px !important;
    text-align: left !important;
    width: 100% !important;
    padding: 11px 12px !important;
    font-family: Georgia, serif !important;
    font-size: 13px !important;
    margin-bottom: 3px !important;
    transition: background 0.15s, color 0.15s;
    line-height: 1.5 !important;
    white-space: pre-line !important;
  }
  div[data-testid="stColumn"]:first-child .stButton button:hover {
    background: rgba(255,255,255,0.10) !important;
    color: #fff !important;
  }
  div[data-testid="stColumn"]:first-child .stButton button[kind="primary"] {
    background: rgba(61,219,176,0.15) !important;
    border-left-color: var(--teal-br) !important;
    color: var(--teal-br) !important;
    font-weight: 600 !important;
  }

  /* Nav labels (group headers) */
  div[data-testid="stColumn"]:first-child p {
    color: rgba(255,255,255,0.88) !important;
  }
  .nav-brand {
    font-family: Georgia, serif; font-size: 15px;
    color: #fff !important; margin-bottom: 2px;
  }
  .nav-sub {
    font-size: 11px; color: rgba(255,255,255,0.45) !important;
    margin-bottom: 0;
  }
  .nav-grp {
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,0.4) !important; font-weight: 700;
    padding: 14px 2px 6px; display: block;
  }
  div[data-testid="stColumn"]:first-child hr {
    border-color: rgba(255,255,255,0.12);
  }

  /* ── Tool header ── */
  .t-hdr {
    padding: 22px 0 18px;
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
    background: var(--white); border: 1px solid var(--border);
    border-radius: 10px; padding: 18px 20px;
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
    border-radius: 12px; padding: 20px 18px; height: 100%;
  }
  .tool-card:hover { box-shadow: none; }
  .tool-icon {
    width: 40px; height: 40px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; margin-bottom: 12px;
  }
  .tool-name {
    font-family: Georgia, serif; font-size: 14px;
    color: var(--navy); margin-bottom: 6px;
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
  .chip-navy   { background: #E8EFF8;   color: var(--navy); }

  /* ── Source pills ── */
  .source-pill {
    display: inline-block; background: var(--tl); color: #0D5F40;
    border-radius: 20px; padding: 3px 11px;
    font-size: 12px; margin: 2px 3px;
    text-decoration: none; white-space: nowrap;
  }
  .source-pill:hover { background: #b2ead8; }

  /* ── Disclaimer ── */
  .disclaimer {
    background: #FEF3D7; border: 1px solid #D4921A;
    border-radius: 8px; padding: 7px 16px;
    font-size: 12px; color: #7A4A00; margin-bottom: 20px;
  }

  /* ── Content column padding ── */
  div[data-testid="stColumn"]:last-child > div:first-child {
    padding: 20px 24px !important;
  }

  /* ── Chat messages ── */
  div[data-testid="stChatMessage"] { max-width: 820px; }
</style>
""", unsafe_allow_html=True)

# ── Load resources ────────────────────────────────────────────────────────────
INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

# ── Session state ─────────────────────────────────────────────────────────────
if "section" not in st.session_state:
    st.session_state["section"] = "overview"
for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []

# ── Top banner ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="topnav-dot"></div>
  <span class="topnav-brand">StrateGPT</span>
  <span class="topnav-div">·</span>
  <span class="topnav-sub">US Program</span>
</div>
""", unsafe_allow_html=True)

# ── Layout: nav column + content column ──────────────────────────────────────
nav_col, content_col = st.columns([1, 4], gap="medium")

# ── Navigation panel ──────────────────────────────────────────────────────────
with nav_col:
    NAV_ITEMS = [
        ("overview",  "🏠", "StrateGPT",           "Overview"),
        ("chat",      "💬", "ChatBot",              "Learn about past and present\nUSP strategy, then test\nyour knowledge"),
        ("explorer",  "📁", "Document Explorer",   "Review key strategy\ndocuments across time"),
        ("synthesis", "🔀", "Strategy Synthesizer","Understand how strategies\nchange and connect"),
    ]

    for key, icon, label, desc in NAV_ITEMS:
        is_active = st.session_state["section"] == key
        if st.button(
            f"{icon}  {label}\n{desc}",
            key=f"nav_{key}",
            type="primary" if is_active else "secondary",
        ):
            st.session_state["section"] = key
            st.rerun()

# ── Content area ──────────────────────────────────────────────────────────────
with content_col:
    st.markdown(
        '<div class="disclaimer">⚠️ Responses generated with AI assistance — '
        'review for accuracy before use. <strong>Internal use only.</strong></div>',
        unsafe_allow_html=True,
    )

    section = st.session_state["section"]

    if section == "overview":
        render_overview()

    elif section == "chat":
        st.markdown(
            '<div class="t-hdr">'
            '<div class="t-ey">SENSEMAKING TOOLS</div>'
            '<div class="t-title">StrateGPT Chat</div>'
            '<div class="t-tag">Ask questions across strategy history, Ambition 2045, '
            'or test your knowledge in Quiz mode.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
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

    elif section == "explorer":
        st.markdown(
            '<div class="t-hdr">'
            '<div class="t-ey">SENSEMAKING TOOLS</div>'
            '<div class="t-title">Document Explorer</div>'
            '<div class="t-tag">Browse, filter, and search all 584 indexed '
            'strategy documents.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_explorer(INDEX, DOC_TEXTS)

    elif section == "synthesis":
        st.markdown(
            '<div class="t-hdr">'
            '<div class="t-ey">SENSEMAKING TOOLS</div>'
            '<div class="t-title">Strategy Synthesizer</div>'
            '<div class="t-tag">Ask cross-cutting questions across multiple strategy '
            'areas and surface shared themes and tensions.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_synthesis(INDEX, DOC_TEXTS, SKILLS, client)
