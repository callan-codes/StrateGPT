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
    padding: 16px 10px !important;
  }

  /* ── Reset: nested first-child columns must NOT inherit nav styling ── */
  div[data-testid="stColumn"] div[data-testid="stColumn"]:first-child > div:first-child {
    background-color: transparent !important;
    border-radius: 0 !important;
    min-height: unset !important;
    padding: 0 !important;
  }
  /* Reset white text inside nested columns (fixes Explorer + Synthesizer) */
  div[data-testid="stColumn"] div[data-testid="stColumn"] p,
  div[data-testid="stColumn"] div[data-testid="stColumn"] label {
    color: var(--text) !important;
  }

  /* ── Nav tile visuals ── */
  .nav-tile {
    display: flex;
    align-items: flex-start;
    gap: 11px;
    padding: 10px 10px;
    border-radius: 8px;
    border-left: 3px solid transparent;
    cursor: pointer;
    transition: background 0.15s;
    margin-bottom: 0;
  }
  .nav-tile:hover { background: rgba(255,255,255,0.08); }
  .nav-tile-active {
    background: rgba(61,219,176,0.12);
    border-left-color: var(--teal-br);
  }
  .nav-tile-icon {
    width: 34px; height: 34px;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0; margin-top: 1px;
  }
  .nav-tile-body { flex: 1; min-width: 0; }
  .nav-tile-label {
    font-family: Georgia, serif;
    font-size: 13px;
    color: #fff;
    line-height: 1.2;
    font-weight: 600;
    margin-bottom: 3px;
  }
  .nav-tile-active .nav-tile-label { color: var(--teal-br); }
  .nav-tile-desc {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    line-height: 1.35;
  }

  /* ── Transparent click overlay for nav tiles ── */
  /* Each tile lives in an st.container() = stVerticalBlock                */
  /* The st.button is absolutely positioned over it, opacity 0             */
  div[data-testid="stVerticalBlock"]:has(.nav-tile) {
    position: relative;
    margin-bottom: 4px !important;
  }
  div[data-testid="stVerticalBlock"]:has(.nav-tile) > div[data-testid="stButton"] {
    position: absolute !important;
    inset: 0 !important;
    z-index: 10 !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  div[data-testid="stVerticalBlock"]:has(.nav-tile) > div[data-testid="stButton"] button {
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
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
    border-radius: 12px; padding: 20px 18px 14px;
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

  /* ── Overview open-tool buttons: small + color-matched ── */
  div[data-testid="stVerticalBlock"]:has(.tc-teal) .stButton button {
    background: #E8F8F4 !important; color: #0B7A62 !important;
    border: 1px solid #aee8d4 !important;
    font-size: 12px !important; padding: 5px 14px !important;
    width: auto !important; border-radius: 6px !important;
    margin-top: 6px !important; box-shadow: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(.tc-teal) .stButton button:hover {
    background: #d0f2e8 !important;
  }
  div[data-testid="stVerticalBlock"]:has(.tc-blue) .stButton button {
    background: #DFF0FF !important; color: #1255A0 !important;
    border: 1px solid #a8d4f7 !important;
    font-size: 12px !important; padding: 5px 14px !important;
    width: auto !important; border-radius: 6px !important;
    margin-top: 6px !important; box-shadow: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(.tc-blue) .stButton button:hover {
    background: #c5e4ff !important;
  }
  div[data-testid="stVerticalBlock"]:has(.tc-purple) .stButton button {
    background: #EEECFF !important; color: #3D2EA0 !important;
    border: 1px solid #cbc8f7 !important;
    font-size: 12px !important; padding: 5px 14px !important;
    width: auto !important; border-radius: 6px !important;
    margin-top: 6px !important; box-shadow: none !important;
  }
  div[data-testid="stVerticalBlock"]:has(.tc-purple) .stButton button:hover {
    background: #dddaff !important;
  }

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
# Each nav item = HTML tile (visual) + transparent st.button (click target).
# CSS positions the button as an absolute overlay over the tile via :has().
NAV_ITEMS = [
    ("overview",  "🏠", "StrateGPT",           "Overview",
     "#E8EFF8", "#0A2240"),
    ("chat",      "💬", "ChatBot",              "Learn about past and present USP strategy, then test your knowledge",
     "#E8F8F4", "#0B9E80"),
    ("explorer",  "📁", "Document Explorer",   "Review key strategy documents across time",
     "#DFF0FF", "#1A6BC4"),
    ("synthesis", "🔀", "Strategy Synthesizer","Understand how strategies change and connect",
     "#EEECFF", "#5E52D4"),
]

with nav_col:
    for nav_key, icon, label, desc, icon_bg, icon_fg in NAV_ITEMS:
        is_active = st.session_state["section"] == nav_key
        active_cls = "nav-tile-active" if is_active else ""
        with st.container():
            st.markdown(f"""
            <div class="nav-tile {active_cls}">
              <div class="nav-tile-icon" style="background:{icon_bg}; color:{icon_fg};">{icon}</div>
              <div class="nav-tile-body">
                <div class="nav-tile-label">{label}</div>
                <div class="nav-tile-desc">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("select", key=f"nav_{nav_key}"):
                st.session_state["section"] = nav_key
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
            '<div class="t-title">ChatBot</div>'
            '<div class="t-tag">Learn about past and present USP strategy, '
            'then test your knowledge in Quiz mode.</div>'
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
