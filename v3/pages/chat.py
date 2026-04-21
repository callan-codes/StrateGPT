"""
Chat page — Strategy History (1A), Ambition 2045 (1B), Quiz Me (1C).
"""
import os, sys, re
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.loader    import load_all, get_client, to_url
from core.retrieval import retrieve
from core.prompts   import build_system, stream_response, get_response, generate_suggestions

INDEX, SKILLS, DOC_TEXTS = load_all()
client = get_client()

for key in ("history_msgs", "amb45_msgs", "quiz_msgs"):
    if key not in st.session_state:
        st.session_state[key] = []
for key in ("history_suggestions", "amb45_suggestions"):
    if key not in st.session_state:
        st.session_state[key] = None


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


def parse_quiz_response(text: str):
    """Returns (question_text, options_dict | None)."""
    m = re.search(r"<<OPTIONS>>(.*?)<<END_OPTIONS>>", text, re.DOTALL)
    if not m:
        return text, None
    question = text[: m.start()].strip()
    options  = {}
    for line in m.group(1).strip().splitlines():
        line = line.strip()
        if len(line) >= 3 and line[1] == ":":
            key = line[0].upper()
            if key in "ABCD":
                options[key] = line[2:].strip()
    return question, options if len(options) >= 2 else None


# ── Chat modes (History & Amb45) ───────────────────────────────────────────────

def run_chat(mode: str, session_key: str, placeholder: str):
    history         = st.session_state[session_key]
    suggestions_key = f"{mode}_suggestions"
    prefill_key     = f"{mode}_prefill"

    # Generate suggestions once per session
    if st.session_state.get(suggestions_key) is None:
        with st.spinner("Generating suggested questions…"):
            st.session_state[suggestions_key] = generate_suggestions(client, mode, SKILLS)

    suggestions = st.session_state.get(suggestions_key) or []

    # Show suggestions only on empty chat
    if suggestions and not history:
        st.caption("Suggested questions — click to ask:")
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            if cols[i].button(q, key=f"{mode}_sug_{i}", use_container_width=True):
                st.session_state[prefill_key] = q
                st.rerun()

    # Render conversation history
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])
            if msg.get("sources"):
                render_sources(msg["sources"])

    # Resolve input: typed message or suggestion click
    prefill = st.session_state.pop(prefill_key, None)
    prompt  = st.chat_input(placeholder) or prefill

    if prompt:
        st.session_state[session_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        docs   = retrieve(prompt, mode, INDEX, DOC_TEXTS)
        system = build_system(mode, docs, DOC_TEXTS, SKILLS)

        with st.chat_message("assistant"):
            full = st.write_stream(stream_response(client, system, history, prompt))
            render_sources(docs)

        st.session_state[session_key].append({"role": "ai", "content": full, "sources": docs})
        if prefill:
            st.rerun()


# ── Quiz Me ────────────────────────────────────────────────────────────────────

QUIZ_TOPICS = [
    "K-12 instructional materials (HQIM)",
    "Postsecondary Success strategy",
    "Pathways & workforce development",
    "Ambition 2045 strategic shifts",
    "Washington State Initiative",
    "USP data & learning strategy",
]


def run_quiz():
    history = st.session_state["quiz_msgs"]

    # Topic suggestions on empty chat
    if not history:
        st.caption("Choose a topic or type your own:")
        cols = st.columns(3)
        for i, topic in enumerate(QUIZ_TOPICS):
            if cols[i % 3].button(topic, key=f"qtopic_{i}", use_container_width=True):
                st.session_state["quiz_prefill"] = f"Quiz me on: {topic}"
                st.rerun()

    # Render message history
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])
            if msg.get("options"):
                for letter, text in msg["options"].items():
                    st.markdown(f"**{letter})** {text}")
            if msg.get("sources"):
                render_sources(msg["sources"])

    # Check if the last message is an unanswered question
    last            = history[-1] if history else None
    pending_options = last and last["role"] == "ai" and last.get("options")
    prefill         = st.session_state.pop("quiz_prefill", None)

    if pending_options and not prefill:
        st.caption("Select your answer:")
        cols = st.columns(4)
        for j, (letter, text) in enumerate(last["options"].items()):
            if cols[j].button(f"{letter}) {text}", key=f"qans_{letter}", use_container_width=True):
                st.session_state["quiz_prefill"] = f"{letter}) {text}"
                st.rerun()
        return  # Don't render chat_input while awaiting MC answer

    prompt = (prefill if prefill else st.chat_input("Type a topic or just say 'start'…"))

    if prompt:
        st.session_state["quiz_msgs"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        docs   = retrieve(prompt, "history", INDEX, DOC_TEXTS)
        system = build_system("quiz", docs, DOC_TEXTS, SKILLS)

        with st.spinner("Thinking…"):
            full_text = get_response(client, system, history, prompt, max_tokens=1000)

        question, options = parse_quiz_response(full_text)

        with st.chat_message("assistant"):
            if options:
                st.markdown(question)
                for letter, text in options.items():
                    st.markdown(f"**{letter})** {text}")
            else:
                st.markdown(full_text)
                render_sources(docs)

        if options:
            st.session_state["quiz_msgs"].append({
                "role": "ai", "content": question, "options": options, "sources": None,
            })
        else:
            st.session_state["quiz_msgs"].append({
                "role": "ai", "content": full_text, "sources": docs,
            })
        st.rerun()


# ── Page layout ────────────────────────────────────────────────────────────────

st.title("Chat")
st.caption("Ask questions about U.S. Program strategy, explore Ambition 2045, or test your knowledge.")

tab1, tab2, tab3 = st.tabs(["📚 Strategy History", "🔭 Ambition 2045", "🧠 Quiz Me"])

with tab1:
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("Clear", key="clr_hist"):
            st.session_state["history_msgs"]        = []
            st.session_state["history_suggestions"] = None
            st.rerun()
    run_chat("history", "history_msgs", "e.g. How has the K-12 strategy evolved since 2019?")

with tab2:
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("Clear", key="clr_amb"):
            st.session_state["amb45_msgs"]        = []
            st.session_state["amb45_suggestions"] = None
            st.rerun()
    run_chat("amb45", "amb45_msgs", "e.g. How does Amb'45 build on prior Postsecondary work?")

with tab3:
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("Clear", key="clr_quiz"):
            st.session_state["quiz_msgs"] = []
            st.rerun()
    run_quiz()
