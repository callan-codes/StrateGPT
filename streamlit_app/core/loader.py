"""
loader.py — document loading and URL conversion.

All heavy I/O is wrapped in @st.cache_resource so it runs exactly once
per server session, regardless of how many users are active or how many
times Streamlit reruns the script.
"""
import json, re, os
from urllib.parse import quote
import streamlit as st
import anthropic

# Repo root — one level above this file's directory (streamlit_app/core/)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SP_DOCS_BASE  = os.environ.get("SP_DOCS_BASE", "")
SP_AMB45_BASE = os.environ.get("SP_AMB45_BASE", "")
LOCAL_DOCS    = "C:/Users/callanco/OneDrive - Gates Foundation/Insight - Strategy Documents/"
LOCAL_AMB45   = "C:/Users/callanco/OneDrive - Gates Foundation/US Program - Ambition 2045 - shared materials/"


def to_url(path: str) -> str:
    """Return a SharePoint URL when deployed, or a local file:// URL for dev."""
    p = path.replace("\\", "/")
    if SP_DOCS_BASE and p.startswith(LOCAL_DOCS):
        return SP_DOCS_BASE.rstrip("/") + "/" + quote(p[len(LOCAL_DOCS):], safe="/") + "?web=1"
    if SP_AMB45_BASE and p.startswith(LOCAL_AMB45):
        return SP_AMB45_BASE.rstrip("/") + "/" + quote(p[len(LOCAL_AMB45):], safe="/") + "?web=1"
    return "file:///" + p


@st.cache_resource(show_spinner="Loading 584 strategy documents…")
def load_all():
    """
    Load document index, skills reference, and extracted document text.
    Returns (index, skills, doc_texts).
    """
    # Document index
    with open(os.path.join(ROOT, "document_index.json"), encoding="utf-8") as f:
        index = json.load(f)["files"]

    # Skills / knowledge base reference
    with open(os.path.join(ROOT, "skills.md"), encoding="utf-8") as f:
        skills = f.read()

    # Extracted document text
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

    ext = os.path.join(ROOT, "extracted_docs.txt")
    amb = os.path.join(ROOT, "amb45_extracted.txt")
    if os.path.exists(ext):
        _load_docx(ext)
    if os.path.exists(amb):
        _load_pdf(amb)

    return index, skills, doc_texts


@st.cache_resource
def get_client():
    """Return a cached Anthropic client."""
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
