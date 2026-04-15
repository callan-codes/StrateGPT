"""
explorer.py — Document Explorer tab.

Lets users browse, filter, and search the full document index.
"""
import pandas as pd
import streamlit as st
from core.retrieval import SKIP_TYPES
from core.loader    import to_url


def _build_dataframe(index: list, doc_texts: dict) -> pd.DataFrame:
    rows = []
    for d in index:
        if d["doc_type"] in SKIP_TYPES:
            continue
        rows.append({
            "Topic":          d["meeting_topic"] or d["filename"],
            "Year":           d["session_year"] or 0,
            "Type":           d["doc_type"] or "unknown",
            "Strategy Areas": ", ".join(d["strategy_areas"]),
            "Has Text":       "✓" if d["filename"] in doc_texts else "",
            "Amb'45":         "✓" if d["is_amb45"] else "",
            "_filename":      d["filename"],
            "_path":          d["path"],
        })
    return pd.DataFrame(rows)


def render_explorer(index: list, doc_texts: dict):
    """Render the Document Explorer tab."""

    st.caption(
        "Browse all 584 indexed strategy documents. Filter by area, year, or type. "
        "Click any row to open the document in SharePoint."
    )

    df = _build_dataframe(index, doc_texts)

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        all_areas  = sorted({a for d in index for a in d["strategy_areas"]})
        area_filter = st.multiselect("Strategy Area", all_areas, placeholder="All areas")

    with col2:
        all_types  = sorted({d["doc_type"] for d in index
                             if d["doc_type"] and d["doc_type"] not in SKIP_TYPES})
        type_filter = st.multiselect("Document Type", all_types, placeholder="All types")

    with col3:
        years = sorted({d["session_year"] for d in index if d["session_year"]})
        if years:
            year_range = st.select_slider(
                "Year range", options=years, value=(min(years), max(years))
            )
        else:
            year_range = None

    with col4:
        amb45_only = st.checkbox("Amb'45 only")

    # ── Keyword search ────────────────────────────────────────────────────────
    search = st.text_input("Search topics / filenames", placeholder="e.g. algebra, postsecondary…")

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()

    if area_filter:
        filtered = filtered[
            filtered["Strategy Areas"].apply(lambda s: any(a in s for a in area_filter))
        ]
    if type_filter:
        filtered = filtered[filtered["Type"].isin(type_filter)]
    if year_range:
        filtered = filtered[
            (filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])
        ]
    if amb45_only:
        filtered = filtered[filtered["Amb'45"] == "✓"]
    if search:
        q = search.lower()
        filtered = filtered[
            filtered["Topic"].str.lower().str.contains(q, na=False) |
            filtered["_filename"].str.lower().str.contains(q, na=False)
        ]

    # ── Stats row ─────────────────────────────────────────────────────────────
    amb_col = "Amb'45"
    c1, c2, c3 = st.columns(3)
    c1.metric("Showing",        f"{len(filtered)} docs")
    c2.metric("With full text", f"{(filtered['Has Text'] == '✓').sum()}")
    c3.metric("Amb'45 docs",    f"{(filtered[amb_col] == '✓').sum()}")

    # ── Table ─────────────────────────────────────────────────────────────────
    display_cols = ["Topic", "Year", "Type", "Strategy Areas", "Has Text", "Amb'45"]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        height=460,
        column_config={
            "Year":           st.column_config.NumberColumn(format="%d", width="small"),
            "Type":           st.column_config.TextColumn(width="medium"),
            "Has Text":       st.column_config.TextColumn(width="small"),
            "Amb'45":         st.column_config.TextColumn(width="small"),
            "Strategy Areas": st.column_config.TextColumn(width="large"),
        },
    )

    # ── Download ──────────────────────────────────────────────────────────────
    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered list as CSV",
        data=csv,
        file_name="strategpt_documents.csv",
        mime="text/csv",
    )
