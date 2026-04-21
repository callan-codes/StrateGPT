"""
Strategy Connector — Sparknotes (3A) and Navigator (3B).
"""
import os, sys, re
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.loader    import load_all, get_client, to_url
from core.retrieval import retrieve
from core.prompts   import build_system, stream_response, get_response

INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

ALL_AREAS    = sorted({a for d in INDEX for a in d["strategy_areas"]})
DEFAULT_AREA = ALL_AREAS[0] if ALL_AREAS else ""


# ── Shared helpers ─────────────────────────────────────────────────────────────

def render_sources(docs: list):
    if not docs:
        return
    with st.expander(f"Sources ({len(docs)})"):
        for d in docs:
            url   = to_url(d["path"])
            label = d["filename"]
            year  = f" ({d['session_year']})" if d["session_year"] else ""
            st.markdown(f"- [{label}{year}]({url})")


def _parse_nav(text: str) -> tuple[str, str]:
    """Return (text_with_anchors, nav_html). Injects <a id> before each bold header."""
    headers = []
    lines   = text.split("\n")
    result  = []
    for line in lines:
        m = re.match(r"^\*\*(.+?)\*\*", line.strip())
        if m:
            header = m.group(1)
            anchor = re.sub(r"[^a-z0-9]+", "-", header.lower()).strip("-")
            headers.append((header, anchor))
            result.append(f'<a id="{anchor}"></a>\n\n{line}')
        else:
            result.append(line)
    anchored = "\n".join(result)

    if not headers:
        return anchored, ""

    links = " &nbsp;·&nbsp; ".join(
        f'<a href="#{a}" style="color:#1A6BC4;text-decoration:none;font-size:13px;">{h}</a>'
        for h, a in headers
    )
    nav = (
        '<div style="background:#F2F7FD;border:1px solid #D8E3F0;border-radius:8px;'
        'padding:10px 16px;margin-bottom:16px;">'
        '<span style="font-size:11px;color:#596577;font-weight:700;letter-spacing:1px;'
        f'text-transform:uppercase;margin-right:10px;">JUMP TO</span>{links}</div>'
    )
    return anchored, nav


# ── Sparknotes (3A) ────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _cached_sparknotes(strategy_area: str, _index, _doc_texts, _skills: str, _client):
    docs   = retrieve(
        f"{strategy_area} strategy history evolution",
        "history", _index, _doc_texts,
        top_n=8, area_filter=[strategy_area],
    )
    system = build_system("sparknotes", docs, _doc_texts, _skills)
    text   = get_response(
        _client, system, [],
        f"Generate a Sparknotes primer on the {strategy_area} strategy.",
        max_tokens=2000,
    )
    return text, docs


def render_sparknotes():
    if "sparknotes_cache" not in st.session_state:
        st.session_state["sparknotes_cache"] = {}

    st.subheader("Strategy Sparknotes")
    st.caption(
        "Select a strategy area to load a concise primer covering key concepts, "
        "how the strategy has evolved, and its connection to Ambition 2045."
    )

    area   = st.selectbox("Strategy area", ALL_AREAS, key="sparknotes_area")
    cached = st.session_state["sparknotes_cache"].get(area)

    if cached:
        text, docs = cached
        anchored, nav = _parse_nav(text)
        if nav:
            st.markdown(nav, unsafe_allow_html=True)
        st.markdown(anchored, unsafe_allow_html=True)
        st.divider()
        render_sources(docs)
    elif st.button("Show Sparknotes", type="primary", key="sparknotes_run"):
        with st.spinner(f"Generating primer on {area}…"):
            text, docs = _cached_sparknotes(area, INDEX, DOC_TEXTS, SKILLS, client)
        st.session_state["sparknotes_cache"][area] = (text, docs)
        st.rerun()
    else:
        st.info("Select a strategy area and click **Show Sparknotes** to get started.", icon="📖")


# ── Navigator (3B) ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _cached_navigator(area: str, _index, _doc_texts, _skills: str, _client):
    docs   = retrieve(
        f"{area} strategy strengths weaknesses opportunities risks tradeoffs",
        "history", _index, _doc_texts,
        top_n=8, area_filter=[area],
    )
    system = build_system("navigator", docs, _doc_texts, _skills)
    query  = (
        f"Analyze the {area} strategy: strengths and opportunities, weaknesses and risks, "
        f"connections to other USP strategies, and anticipated tradeoffs for 2026."
    )
    text = get_response(_client, system, [], query, max_tokens=2000)
    return text, docs


def render_navigator():
    if "navigator_cache" not in st.session_state:
        st.session_state["navigator_cache"] = {}

    st.subheader("Strategy Navigator")
    st.caption(
        "Select a strategy area to explore its strengths, risks, connections to other strategies, "
        "and anticipated tradeoffs heading into 2026."
    )

    area   = st.selectbox("Strategy area", ALL_AREAS, key="navigator_area")
    cached = st.session_state["navigator_cache"].get(area)

    if cached:
        text, docs = cached
        anchored, nav = _parse_nav(text)
        if nav:
            st.markdown(nav, unsafe_allow_html=True)
        st.markdown(anchored, unsafe_allow_html=True)
        st.divider()
        render_sources(docs)
    elif st.button("Analyze Strategy", type="primary", key="navigator_run"):
        with st.spinner(f"Analyzing {area}…"):
            text, docs = _cached_navigator(area, INDEX, DOC_TEXTS, SKILLS, client)
        st.session_state["navigator_cache"][area] = (text, docs)
        st.rerun()
    else:
        st.info("Select a strategy area and click **Analyze Strategy** to get started.", icon="🔀")


# ── Page layout ────────────────────────────────────────────────────────────────

st.title("Strategy Connector")

tab1, tab2 = st.tabs(["📖 Strategy Sparknotes", "🧭 Strategy Navigator"])

with tab1:
    render_sparknotes()

with tab2:
    render_navigator()
