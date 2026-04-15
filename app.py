import json, re, os
import pandas as pd
from urllib.parse import quote
from dotenv import load_dotenv
import streamlit as st
import anthropic

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StrateGPT — USP Strategy Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  section[data-testid="stSidebar"] { background-color: #1D2530 !important; }
  section[data-testid="stSidebar"] *,
  section[data-testid="stSidebar"] .stRadio label span { color: #ffffff !important; }
  section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }
  .stChatMessage { max-width: 820px; }
  .source-pill {
    display: inline-block; background: #D4F5EF; color: #1A7A6E;
    border-radius: 20px; padding: 2px 10px; font-size: 12px; margin: 2px 3px;
    text-decoration: none;
  }
  .source-pill:hover { background: #b2eee4; }
  .disclaimer {
    background: #FBF5CC; border: 1px solid #d4a800;
    border-radius: 8px; padding: 8px 14px;
    font-size: 12px; color: #7a5500; margin-bottom: 12px;
  }
</style>
""", unsafe_allow_html=True)

# ── Paths & env ───────────────────────────────────────────────────────────────
BASE          = os.path.dirname(os.path.abspath(__file__))
SP_DOCS_BASE  = os.environ.get("SP_DOCS_BASE", "")
SP_AMB45_BASE = os.environ.get("SP_AMB45_BASE", "")
LOCAL_DOCS    = "C:/Users/callanco/OneDrive - Gates Foundation/Insight - Strategy Documents/"
LOCAL_AMB45   = "C:/Users/callanco/OneDrive - Gates Foundation/US Program - Ambition 2045 - shared materials/"

def to_url(path: str) -> str:
    p = path.replace("\\", "/")
    if SP_DOCS_BASE and p.startswith(LOCAL_DOCS):
        return SP_DOCS_BASE.rstrip("/") + "/" + quote(p[len(LOCAL_DOCS):], safe="/") + "?web=1"
    if SP_AMB45_BASE and p.startswith(LOCAL_AMB45):
        return SP_AMB45_BASE.rstrip("/") + "/" + quote(p[len(LOCAL_AMB45):], safe="/") + "?web=1"
    return "file:///" + p

# ── Resource loading (runs once; Streamlit shows spinner automatically) ───────
@st.cache_resource(show_spinner="Loading 584 strategy documents…")
def load_all():
    with open(os.path.join(BASE, "document_index.json"), encoding="utf-8") as f:
        index = json.load(f)["files"]

    with open(os.path.join(BASE, "skills.md"), encoding="utf-8") as f:
        skills = f.read()

    doc_texts: dict[str, str] = {}

    def _load_docx(filepath):
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        ms = list(re.finditer(r"---\s*(.+?\.docx)\s*---", content))
        for i, m in enumerate(ms):
            fname = os.path.basename(m.group(1).strip())
            end   = ms[i + 1].start() if i + 1 < len(ms) else len(content)
            doc_texts[fname] = content[m.start():end]

    def _load_pdf(filepath):
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        ms = list(re.finditer(r"FILE:\s*(.+)", content))
        for i, m in enumerate(ms):
            fname = os.path.basename(m.group(1).strip())
            end   = ms[i + 1].start() if i + 1 < len(ms) else len(content)
            doc_texts[fname] = content[m.start():end]

    if os.path.exists(os.path.join(BASE, "extracted_docs.txt")):
        _load_docx(os.path.join(BASE, "extracted_docs.txt"))
    if os.path.exists(os.path.join(BASE, "amb45_extracted.txt")):
        _load_pdf(os.path.join(BASE, "amb45_extracted.txt"))

    return index, skills, doc_texts

@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

# ── Retrieval ─────────────────────────────────────────────────────────────────
SKIP_TYPES = {"appendix", "table-of-contents", "acronym-list", "participant-bios", "org-chart"}

def _score(doc, query_lower, tokens, mode, area_filter=None):
    if doc["doc_type"] in SKIP_TYPES:
        return 0
    if area_filter and not any(a in doc["strategy_areas"] for a in area_filter):
        return 0
    score = 0
    if mode == "amb45":
        score += 10 if doc["is_amb45"] else -3
    name = doc["filename"].lower() + " " + doc["meeting_topic"].lower()
    for t in tokens:
        if t in name:
            score += 2
    for concept in doc["concepts"]:
        if any(t in concept.lower() for t in tokens):
            score += 3
    for area in doc["strategy_areas"]:
        if area.lower() in query_lower:
            score += 2
    if doc["filename"] in DOC_TEXTS:
        score += 1
    return score

def retrieve(query, mode, top_n=5, area_filter=None):
    q    = query.lower()
    toks = re.findall(r"\b\w{4,}\b", q)
    scored = sorted(
        ((s, d) for d in INDEX if (s := _score(d, q, toks, mode, area_filter)) > 0),
        key=lambda x: -x[0],
    )
    return [d for _, d in scored[:top_n]]

# ── Streaming chat helper ─────────────────────────────────────────────────────
MODE_INSTRUCTIONS = {
    "history": (
        "Answer questions about U.S. Program strategy history. Draw on the retrieved documents "
        "for specific, grounded answers. Reference document names and years. Highlight how "
        "strategies evolved over time when relevant."
    ),
    "amb45": (
        "Help the user understand Ambition 2045 and its connections to historical USP strategies. "
        "Reference specific legacy programs and how past investments laid groundwork for each "
        "Amb'45 priority. Be concrete about which priorities map to which legacy strategy areas."
    ),
    "quiz": (
        "You are in Quiz Mode. Generate multiple-choice questions (A–D) that test understanding "
        "of USP strategy concepts. Present one question at a time. After the user answers, "
        "explain whether they're correct and why, then ask if they'd like another question."
    ),
    "synthesis": (
        "The user wants a cross-strategy synthesis. Draw explicitly on documents from EACH of the "
        "selected strategy areas. Identify shared themes, tensions, and how the strategies "
        "complement or differ from each other. Be specific about which insights come from which area."
    ),
}

def build_system(mode, docs):
    parts = []
    for doc in docs:
        raw = DOC_TEXTS.get(doc["filename"], "")
        if raw:
            body = "\n".join(raw.split("\n")[1:]).strip()[:3000]
            year = str(doc["session_year"]) if doc["session_year"] else "undated"
            parts.append(f"[{doc['filename']} | {year} | {', '.join(doc['strategy_areas'])}]\n{body}")
    context = "\n\n---\n\n".join(parts) or "No extracted text available."
    return (
        f"You are StrateGPT, an AI assistant for Gates Foundation U.S. Program (USP) strategy.\n\n"
        f"## USP Strategy Knowledge Base\n{SKILLS}\n\n"
        f"## Retrieved Documents\n{context}\n\n"
        f"## Instructions\n{MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['history'])}\n\n"
        "Cite documents by name and year. Acknowledge uncertainty rather than speculating.\n"
        "Use **bold** for headers. Use plain bullet points. No markdown tables or horizontal rules."
    )

def stream_response(system, history, message):
    api_msgs = []
    for h in history[-6:]:
        role    = "assistant" if h["role"] == "ai" else "user"
        content = h.get("content", "")
        if content:
            api_msgs.append({"role": role, "content": content})
    api_msgs.append({"role": "user", "content": message})
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=api_msgs,
    ) as stream:
        yield from stream.text_stream

def render_sources(docs):
    if not docs:
        return
    pills = []
    for d in docs:
        url   = to_url(d["path"])
        label = (d["meeting_topic"] or d["filename"])[:45]
        year  = f" ({d['session_year']})" if d["session_year"] else ""
        if url.startswith("file"):
            pills.append(f'<span class="source-pill">📄 {label}{year}</span>')
        else:
            pills.append(f'<a class="source-pill" href="{url}" target="_blank">📄 {label}{year}</a>')
    st.markdown(" ".join(pills), unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 StrateGPT")
    st.markdown("**U.S. Program Strategy Assistant**")
    st.markdown("---")

    mode = st.radio(
        "Mode",
        options=["Strategy History", "Ambition 2045", "Quiz Me"],
        index=0,
        key="mode_radio",
    )

    st.markdown("---")
    st.markdown(f"**Knowledge Base**")
    st.markdown(f"📚 **{len(INDEX)}** strategy documents")
    st.markdown(f"📝 **{len(DOC_TEXTS)}** with extracted text")
    st.markdown("*2019 – 2026 · K-12 · PS · Pathways · Data · Amb'45*")

    st.markdown("---")
    mode_key = {"Strategy History": "history_msgs", "Ambition 2045": "amb45_msgs", "Quiz Me": "quiz_msgs"}[mode]
    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state[mode_key] = []
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<div class="disclaimer">⚠️ Responses generated with AI assistance. Review for accuracy before use. <strong>Internal use only.</strong></div>', unsafe_allow_html=True)

tab_chat, tab_explorer, tab_synthesis = st.tabs(["💬 Chat", "📁 Document Explorer", "🔀 Strategy Synthesis"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════════════════════════════
with tab_chat:
    backend_mode = {"Strategy History": "history", "Ambition 2045": "amb45", "Quiz Me": "quiz"}[mode]
    history = st.session_state[mode_key]

    MODE_META = {
        "Strategy History": ("📚", "Ask any question about U.S. Program strategies from 2019 to present."),
        "Ambition 2045":    ("🔭", "Explore how Ambition 2045 connects to — and departs from — historical USP strategy."),
        "Quiz Me":          ("🧠", "Type a topic to be quizzed on, or just say 'start' to begin."),
    }
    icon, desc = MODE_META[mode]
    st.markdown(f"### {icon} {mode}")
    st.caption(desc)

    # Render conversation history
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role, avatar=("👤" if role == "user" else "🤖")):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"📎 {len(msg['sources'])} source(s)"):
                    render_sources(msg["sources"])

    # Input
    prompt = st.chat_input(
        placeholder={
            "Strategy History": "e.g. How has the Postsecondary Success strategy evolved since 2019?",
            "Ambition 2045":    "e.g. How does Amb'45 build on prior Postsecondary work?",
            "Quiz Me":          "e.g. Quiz me on K-12 Education strategy",
        }[mode]
    )

    if prompt:
        st.session_state[mode_key].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        docs = retrieve(prompt, backend_mode)
        system = build_system(backend_mode, docs)

        with st.chat_message("assistant", avatar="🤖"):
            full_response = st.write_stream(stream_response(system, history, prompt))
            if docs:
                with st.expander(f"📎 {len(docs)} source(s)"):
                    render_sources(docs)

        st.session_state[mode_key].append({
            "role": "ai",
            "content": full_response,
            "sources": docs,
        })

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT EXPLORER
# ════════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    st.markdown("### 📁 Document Explorer")
    st.caption("Browse and filter all 584 indexed strategy documents.")

    # Build dataframe
    rows = []
    for d in INDEX:
        if d["doc_type"] in SKIP_TYPES:
            continue
        rows.append({
            "Filename":       d["filename"],
            "Topic":          d["meeting_topic"] or "—",
            "Year":           d["session_year"] or 0,
            "Type":           d["doc_type"],
            "Strategy Areas": ", ".join(d["strategy_areas"]),
            "Has Text":       "✓" if d["filename"] in DOC_TEXTS else "",
            "Amb'45":         "✓" if d["is_amb45"] else "",
            "_path":          d["path"],
        })
    df = pd.DataFrame(rows)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        all_areas = sorted({a for d in INDEX for a in d["strategy_areas"]})
        area_filter = st.multiselect("Strategy Area", all_areas, placeholder="All areas")
    with col2:
        years = sorted({d["session_year"] for d in INDEX if d["session_year"]})
        year_range = st.select_slider("Year", options=years, value=(min(years), max(years))) if years else None
    with col3:
        all_types = sorted({d["doc_type"] for d in INDEX if d["doc_type"] not in SKIP_TYPES})
        type_filter = st.multiselect("Document Type", all_types, placeholder="All types")

    filtered = df.copy()
    if area_filter:
        filtered = filtered[filtered["Strategy Areas"].apply(lambda s: any(a in s for a in area_filter))]
    if year_range:
        filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
    if type_filter:
        filtered = filtered[filtered["Type"].isin(type_filter)]

    st.caption(f"Showing **{len(filtered)}** of {len(df)} documents")

    display_cols = ["Topic", "Year", "Type", "Strategy Areas", "Has Text", "Amb'45"]
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "Year":           st.column_config.NumberColumn(format="%d"),
            "Has Text":       st.column_config.TextColumn(width="small"),
            "Amb'45":         st.column_config.TextColumn(width="small"),
            "Strategy Areas": st.column_config.TextColumn(width="medium"),
        },
    )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — STRATEGY SYNTHESIS
# ════════════════════════════════════════════════════════════════════════════════
with tab_synthesis:
    st.markdown("### 🔀 Strategy Synthesis")
    st.caption(
        "Ask a cross-cutting question and StrateGPT will draw on documents from each selected "
        "strategy area to synthesize a response — surfacing shared themes, tensions, and connections."
    )

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("**Select strategy areas to synthesize across:**")
        synth_areas = st.multiselect(
            "Strategy Areas",
            options=sorted({a for d in INDEX for a in d["strategy_areas"]}),
            default=["K-12 Education", "Postsecondary Success"],
            label_visibility="collapsed",
        )

        synth_prompt = st.text_area(
            "Your question",
            placeholder="e.g. How do the K-12 and Postsecondary strategies each approach equity for low-income students — and where do they diverge?",
            height=120,
        )

        synth_btn = st.button("✨ Synthesize", type="primary", disabled=not (synth_areas and synth_prompt))

        st.markdown("**Sample questions:**")
        samples = [
            "How do these strategies each define and measure equity?",
            "Where do these strategies reinforce each other, and where are the tensions?",
            "How has AI shaped thinking across these strategy areas?",
            "What role does data infrastructure play in each strategy?",
        ]
        for s in samples:
            if st.button(s, key=f"synth_{s[:20]}", use_container_width=True):
                synth_prompt = s
                synth_btn = True

    with col_right:
        if synth_btn and synth_areas and synth_prompt:
            docs = retrieve(synth_prompt, "history", top_n=8, area_filter=synth_areas)
            system = build_system("synthesis", docs)

            area_labels = " · ".join(synth_areas)
            st.markdown(f"**Synthesizing across:** {area_labels}")
            st.markdown(f"*Drawing on {len(docs)} retrieved documents*")
            st.markdown("---")

            with st.spinner(""):
                response_placeholder = st.empty()
                full_text = ""
                for chunk in stream_response(system, [], synth_prompt):
                    full_text += chunk
                    response_placeholder.markdown(full_text + "▌")
                response_placeholder.markdown(full_text)

            if docs:
                st.markdown("---")
                st.markdown("**Sources retrieved:**")
                render_sources(docs)
        else:
            st.info("Select strategy areas and enter a question to get a cross-strategy synthesis.", icon="ℹ️")
