"""
overview.py — StrateGPT overview / landing page.
"""
import streamlit as st


def render_overview():
    st.markdown("""
    <div class="t-hdr">
      <div class="t-ey">GATES FOUNDATION · U.S. PROGRAM</div>
      <div class="t-title">StrateGPT</div>
      <div class="t-tag">Deepen your strategy knowledge – understand key concepts,
      identify shifts over time, and surface connections between workstreams.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tool cards ────────────────────────────────────────────────────────────
    st.markdown('<div class="card-ey" style="margin-bottom:10px;">SENSEMAKING TOOLS</div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="tool-card tc-teal">
          <div class="tool-icon" style="background:#E8F8F4; color:#0B9E80;">💬</div>
          <div class="tool-name">ChatBot</div>
          <div class="tool-desc">Learn about past and present USP strategy,
          then test your knowledge in Quiz mode.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open ChatBot →", key="open_chat"):
            st.session_state["section"] = "chat"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="tool-card tc-blue">
          <div class="tool-icon" style="background:#DFF0FF; color:#1A6BC4;">📁</div>
          <div class="tool-name">Document Explorer</div>
          <div class="tool-desc">Review key strategy documents across time —
          filter by area, year, and document type.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Document Explorer →", key="open_explorer"):
            st.session_state["section"] = "explorer"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="tool-card tc-purple">
          <div class="tool-icon" style="background:#EEECFF; color:#5E52D4;">🔀</div>
          <div class="tool-name">Strategy Synthesizer</div>
          <div class="tool-desc">Understand how strategies change and connect —
          ask cross-cutting questions across multiple workstreams.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Strategy Synthesizer →", key="open_synthesis"):
            st.session_state["section"] = "synthesis"
            st.rerun()

    st.markdown("---")

    # ── Knowledge base stats ──────────────────────────────────────────────────
    st.markdown('<div class="card-ey" style="margin-bottom:10px;">KNOWLEDGE BASE</div>',
                unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Documents", "584")
    m2.metric("With Extracted Text", "364")
    m3.metric("Years Covered", "2019–2026")
    m4.metric("Strategy Areas", "7")

    st.markdown("""
    <div class="card" style="margin-top:16px;">
      <div class="card-ey">STRATEGY AREAS</div>
      <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;">
        <span class="chip chip-teal">K-12 Education</span>
        <span class="chip chip-blue">Postsecondary Success</span>
        <span class="chip chip-purple">Pathways</span>
        <span class="chip chip-navy">Data Strategy</span>
        <span class="chip chip-teal">Charter Schools</span>
        <span class="chip chip-blue">Washington State</span>
        <span class="chip chip-purple">Ambition 2045</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
