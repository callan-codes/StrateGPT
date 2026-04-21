"""
loader.py — document index, skills reference, and extracted text.
All heavy I/O is @st.cache_resource so it runs once per process.
"""
import json, re, os
from urllib.parse import quote
import streamlit as st
import anthropic

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


@st.cache_resource(show_spinner="Loading strategy documents…")
def load_all():
    with open(os.path.join(ROOT, "document_index.json"), encoding="utf-8") as f:
        index = json.load(f)["files"]

    with open(os.path.join(ROOT, "skills.md"), encoding="utf-8") as f:
        skills = f.read()

    doc_texts: dict[str, str] = {}

    def _load_docx(fp):
        with open(fp, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        ms = list(re.finditer(r"---\s*(.+?\.docx)\s*---", txt))
        for i, m in enumerate(ms):
            fname = os.path.basename(m.group(1).strip())
            end   = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
            doc_texts[fname] = txt[m.start():end]

    def _load_pdf(fp):
        with open(fp, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        ms = list(re.finditer(r"FILE:\s*(.+)", txt))
        for i, m in enumerate(ms):
            fname = os.path.basename(m.group(1).strip())
            end   = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
            doc_texts[fname] = txt[m.start():end]

    for path, loader in [
        (os.path.join(ROOT, "extracted_docs.txt"),    _load_docx),
        (os.path.join(ROOT, "amb45_extracted.txt"),   _load_pdf),
        (os.path.join(ROOT, "pdf_pptx_extracted.txt"),_load_pdf),
    ]:
        if os.path.exists(path):
            loader(path)

    return index, skills, doc_texts


@st.cache_resource
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
