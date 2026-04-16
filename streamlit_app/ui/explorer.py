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
            "Document":       d["meeting_topic"] or d["filename"],
            "Year":           d["session_year"] or 0,
            "Type":           d["doc_type"] or "unknown",
            "Strategy Areas": ", ".join(d["strategy_areas"]),
            "Amb'45":         "✓" if d["is_amb45"] else "",
            "_filename":      d["filename"],
            "_url":           to_url(d["path"]),
        })
    return pd.DataFrame(rows)


def _render_table(filtered: pd.DataFrame):
    """Render filtered documents as an HTML table with clickable document names."""
    rows_html = []
    for _, row in filtered.iterrows():
        url  = row["_url"]
        name = row["Document"]
        year = int(row["Year"]) if row["Year"] else "—"
        doc_type = row["Type"]
        areas = row["Strategy Areas"]
        amb   = row["Amb'45"]

        if url.startswith("file"):
            doc_cell = f'<td class="ex-doc">{name}</td>'
        else:
            doc_cell = f'<td class="ex-doc"><a href="{url}" target="_blank">{name}</a></td>'

        rows_html.append(
            f"<tr>"
            f"{doc_cell}"
            f'<td class="ex-sm">{year}</td>'
            f'<td class="ex-sm">{doc_type}</td>'
            f'<td class="ex-areas">{areas}</td>'
            f'<td class="ex-sm" style="text-align:center;">{amb}</td>'
            f"</tr>"
        )

    table = f"""
    <style>
      .ex-wrap {{ overflow-y: auto; max-height: 480px; border: 1px solid var(--border);
                  border-radius: 8px; margin-top: 12px; }}
      .ex-tbl {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
      .ex-tbl thead th {{ background: var(--surf); color: var(--muted); font-size: 11px;
                          letter-spacing: 0.8px; text-transform: uppercase; font-weight: 700;
                          padding: 10px 12px; position: sticky; top: 0; z-index: 1;
                          border-bottom: 1px solid var(--border); text-align: left; }}
      .ex-tbl tbody tr {{ border-bottom: 1px solid var(--border); }}
      .ex-tbl tbody tr:hover {{ background: var(--surf); }}
      .ex-tbl td {{ padding: 9px 12px; color: var(--text); vertical-align: top; }}
      .ex-doc {{ max-width: 360px; word-break: break-word; }}
      .ex-doc a {{ color: var(--blue); text-decoration: none; }}
      .ex-doc a:hover {{ text-decoration: underline; }}
      .ex-sm {{ white-space: nowrap; color: var(--muted); }}
      .ex-areas {{ font-size: 12px; color: var(--muted); max-width: 220px; }}
    </style>
    <div class="ex-wrap">
      <table class="ex-tbl">
        <thead>
          <tr>
            <th>Document</th>
            <th>Year</th>
            <th>Type</th>
            <th>Strategy Areas</th>
            <th>Amb'45</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table, unsafe_allow_html=True)


def render_explorer(index: list, doc_texts: dict):
    """Render the Document Explorer tab."""

    st.caption(
        "Browse all 584 indexed strategy documents. Filter by area, year, or type. "
        "Click any document name to open it in SharePoint."
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
        amb_col = "Amb'45"
        filtered = filtered[filtered[amb_col] == "✓"]
    if search:
        q = search.lower()
        filtered = filtered[
            filtered["Document"].str.lower().str.contains(q, na=False) |
            filtered["_filename"].str.lower().str.contains(q, na=False)
        ]

    # ── Stats row ─────────────────────────────────────────────────────────────
    amb_col = "Amb'45"
    c1, c2 = st.columns(2)
    c1.metric("Showing", f"{len(filtered)} docs")
    c2.metric("Amb'45 docs", f"{(filtered[amb_col] == '✓').sum()}")

    # ── Table ─────────────────────────────────────────────────────────────────
    _render_table(filtered)

    # ── Download ──────────────────────────────────────────────────────────────
    csv_cols = ["Document", "Year", "Type", "Strategy Areas", "Amb'45"]
    csv = filtered[csv_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered list as CSV",
        data=csv,
        file_name="strategpt_documents.csv",
        mime="text/csv",
    )
