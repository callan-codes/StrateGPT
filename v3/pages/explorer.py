"""
Document Explorer — hyperlinked repository of all indexed strategy documents.
"""
import os, sys, html as _html
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.loader import load_all, to_url, SP_DOCS_BASE, SP_AMB45_BASE

INDEX, SKILLS, DOC_TEXTS = load_all()

sp_configured = bool(SP_DOCS_BASE or SP_AMB45_BASE)


def _build_df() -> pd.DataFrame:
    rows = []
    for d in INDEX:
        raw_year = d["session_year"] or 0
        rows.append({
            "Document":       d["filename"],
            "Year":           2026 if raw_year == 2030 else raw_year,
            "Type":           d["doc_type"] or "other",
            "Strategy Areas": ", ".join(d["strategy_areas"]),
            "Key Concepts":   ", ".join(d["concepts"][:6]) if d["concepts"] else "",
            "Amb'45":         "Yes" if d["is_amb45"] else "",
            "_url":           to_url(d["path"]),
            "_filename":      d["filename"],
        })
    return pd.DataFrame(rows)


def _table_html(df: pd.DataFrame) -> str:
    rows = []
    for _, r in df.iterrows():
        url  = r["_url"]
        doc  = _html.escape(r["Document"])
        year = int(r["Year"]) if r["Year"] else "—"
        rows.append(
            f'<tr>'
            f'<td><a href="{url}" target="_blank">{doc}</a></td>'
            f'<td style="white-space:nowrap">{year}</td>'
            f'<td>{_html.escape(r["Type"])}</td>'
            f'<td>{_html.escape(r["Strategy Areas"])}</td>'
            f'<td>{_html.escape(r["Key Concepts"])}</td>'
            f'<td style="text-align:center">{r["Amb\'45"]}</td>'
            f'</tr>'
        )
    thead = (
        '<thead><tr>'
        '<th>Document</th><th>Year</th><th>Type</th>'
        '<th>Strategy Areas</th><th>Key Concepts</th><th>Amb\'45</th>'
        '</tr></thead>'
    )
    return (
        '<style>'
        '.dt{width:100%;border-collapse:collapse;font-size:13px;}'
        '.dt th{background:#F2F7FD;color:#596577;font-size:11px;letter-spacing:.8px;'
        'text-transform:uppercase;padding:8px 12px;text-align:left;'
        'border-bottom:2px solid #D8E3F0;}'
        '.dt td{padding:7px 12px;border-bottom:1px solid #F0F4F8;vertical-align:top;}'
        '.dt tr:hover td{background:#FAFCFF;}'
        '.dt a{color:#1A6BC4;text-decoration:none;}'
        '.dt a:hover{text-decoration:underline;}'
        '</style>'
        f'<table class="dt">{thead}<tbody>{"".join(rows)}</tbody></table>'
    )


# ── Page ───────────────────────────────────────────────────────────────────────

st.title("Document Explorer")
st.caption(
    "Browse all indexed strategy documents. "
    + ("Click a document title to open in SharePoint." if sp_configured
       else "⚠️ Set SP_DOCS_BASE in your .env to enable SharePoint links.")
)

df = _build_df()

# ── Filters ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    all_areas = sorted({a for d in INDEX for a in d["strategy_areas"]})
    area_sel  = st.multiselect("Strategy Area", all_areas, placeholder="All areas")

with col2:
    all_types = sorted({d["doc_type"] for d in INDEX if d["doc_type"]})
    type_sel  = st.multiselect("Document Type", all_types, placeholder="All types")

with col3:
    years = sorted({d["session_year"] for d in INDEX if d["session_year"]})
    if years:
        year_range = st.select_slider("Year range", options=years, value=(min(years), max(years)))
    else:
        year_range = None

with col4:
    amb_only = st.checkbox("Amb'45 only")

search = st.text_input("Search documents", placeholder="e.g. algebra, postsecondary, pathways…")

# ── Apply filters ───────────────────────────────────────────────────────────────
filtered = df.copy()

if area_sel:
    filtered = filtered[filtered["Strategy Areas"].apply(lambda s: any(a in s for a in area_sel))]
if type_sel:
    filtered = filtered[filtered["Type"].isin(type_sel)]
if year_range:
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
if amb_only:
    filtered = filtered[filtered["Amb'45"] == "Yes"]
if search:
    q = search.lower()
    filtered = filtered[
        filtered["Document"].str.lower().str.contains(q, na=False) |
        filtered["_filename"].str.lower().str.contains(q, na=False) |
        filtered["Key Concepts"].str.lower().str.contains(q, na=False)
    ]

# ── Stats ────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Showing",        f"{len(filtered)} docs")
c2.metric("With full text", f"{filtered['_filename'].isin(DOC_TEXTS).sum()}")
c3.metric("Amb'45 docs",    str((filtered["Amb'45"] == "Yes").sum()))

# ── Table ──────────────────────────────────────────────────────────────────────
st.markdown(_table_html(filtered), unsafe_allow_html=True)

# ── Download ────────────────────────────────────────────────────────────────────
csv = filtered[["Document", "Year", "Type", "Strategy Areas", "Key Concepts", "Amb'45"]].to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered list (CSV)",
    data=csv,
    file_name="strategpt_documents.csv",
    mime="text/csv",
)
