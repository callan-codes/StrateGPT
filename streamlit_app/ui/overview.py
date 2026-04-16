"""
overview.py — Strategy Assistant overview / landing page.
Content can be populated by the user.
"""
import streamlit as st


def render_overview():
    st.markdown("""
    <div class="t-hdr">
      <div class="t-ey">GATES FOUNDATION · U.S. PROGRAM</div>
      <div class="t-title">Strategy Assistant</div>
      <div class="t-tag">Navigate, explore, and synthesize U.S. Program strategy across
      584 documents spanning 2019–2026.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── About section ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="card" style="margin-bottom:18px;">
      <div class="card-ey">ABOUT</div>
      <div class="card-title">What is StrateGPT?</div>
      <div class="card-body">
        <em>Content coming soon — add your overview text here.</em>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tool cards ────────────────────────────────────────────────────────────
    st.markdown('<div class="card-ey" style="margin-bottom:10px;">SENSEMAKING TOOLS</div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="tool-card">
          <div class="tool-icon" style="background:#E8F8F4; color:#0B9E80;">💬</div>
          <div class="tool-name">StrateGPT Chat</div>
          <div class="tool-desc">Ask questions across Strategy History, Ambition 2045,
          or test your knowledge in Quiz mode.</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="tool-card">
          <div class="tool-icon" style="background:#DFF0FF; color:#1A6BC4;">📁</div>
          <div class="tool-name">Document Explorer</div>
          <div class="tool-desc">Browse, filter, and search all 584 indexed strategy
          documents by area, year, and type.</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="tool-card">
          <div class="tool-icon" style="background:#EEECFF; color:#5E52D4;">🔀</div>
          <div class="tool-name">Strategy Synthesizer</div>
          <div class="tool-desc">Ask cross-cutting questions across multiple strategy
          areas and surface shared themes and tensions.</div>
        </div>
        """, unsafe_allow_html=True)

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
