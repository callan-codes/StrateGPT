"""
synthesis.py — Strategy Synthesis tab.

Users select multiple strategy areas and ask a cross-cutting question.
Retrieval pulls documents from all selected areas; the prompt instructs
Claude to synthesize explicitly across them.
"""
import streamlit as st
from core.retrieval import retrieve
from core.prompts   import build_system, stream_response
from core.loader    import to_url

DOC_ICONS = {
    "memo": "📄", "cover-note": "📄", "email": "📧",
    "presentation": "📊", "meeting-notes": "📝",
    "pre-read": "📖", "digital-binder": "📁",
}

SAMPLE_QUESTIONS = [
    "How do these strategies each define and measure equity for low-income students?",
    "Where do these strategies reinforce each other, and where are the tensions?",
    "How has AI shaped thinking across these strategy areas?",
    "What role does data infrastructure play across these strategies?",
    "How have these strategies evolved in response to COVID-19?",
    "Which grantees and partners appear across multiple strategy areas?",
]


def _render_sources(docs: list):
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


def render_synthesis(index: list, doc_texts: dict, skills: str, client):
    """Render the Strategy Synthesis tab."""

    st.caption(
        "Select two or more strategy areas, then ask a cross-cutting question. "
        "StrateGPT will draw on documents from each area and synthesize a response "
        "that highlights shared themes, divergences, and connections."
    )

    # ── Controls ──────────────────────────────────────────────────────────────
    all_areas = sorted({a for d in index for a in d["strategy_areas"]})

    col_left, col_right = st.columns([1, 2], gap="large")

    with col_left:
        st.markdown("**1. Select strategy areas**")
        selected_areas = st.multiselect(
            "Areas",
            options=all_areas,
            default=["K-12 Education", "Postsecondary Success"],
            label_visibility="collapsed",
        )

        st.markdown("**2. Ask your question**")
        question = st.text_area(
            "Question",
            placeholder="e.g. How do these strategies each approach equity for low-income students — and where do they diverge?",
            height=110,
            label_visibility="collapsed",
        )

        run = st.button(
            "✨ Synthesize",
            type="primary",
            disabled=not (len(selected_areas) >= 2 and question.strip()),
            use_container_width=True,
        )
        if len(selected_areas) < 2:
            st.caption("Select at least two strategy areas to synthesize.")

        st.markdown("---")
        st.markdown("**Sample questions:**")
        for sample in SAMPLE_QUESTIONS:
            if st.button(sample, key=f"s_{sample[:24]}", use_container_width=True):
                # Store in session state so it populates on next rerun
                st.session_state["synth_prefill"] = sample
                st.rerun()

    # Handle prefill from sample button
    if "synth_prefill" in st.session_state:
        question = st.session_state.pop("synth_prefill")
        run = True

    # ── Response area ─────────────────────────────────────────────────────────
    with col_right:
        if run and selected_areas and question.strip():
            docs   = retrieve(question, "history", index, doc_texts,
                              top_n=8, area_filter=selected_areas)
            system = build_system("synthesis", docs, doc_texts, skills)

            area_str = " · ".join(selected_areas)
            st.markdown(f"**Synthesizing across:** {area_str}")
            st.caption(f"Drawing on {len(docs)} retrieved documents")
            st.divider()

            full_text = st.write_stream(
                stream_response(client, system, [], question)
            )

            if docs:
                st.divider()
                st.markdown("**Sources retrieved:**")
                _render_sources(docs)

        elif not run:
            st.info(
                "Select at least two strategy areas and enter a question to get started.",
                icon="ℹ️",
            )
