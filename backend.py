import json, re, os
from urllib.parse import quote
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths (relative to this file so they work both locally and on Azure) ─────
BASE        = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE  = os.path.join(BASE, "document_index.json")
EXTRACTED   = os.path.join(BASE, "extracted_docs.txt")
AMB45_EXT   = os.path.join(BASE, "amb45_extracted.txt")
SKILLS_FILE = os.path.join(BASE, "skills.md")

# ── SharePoint URL conversion ─────────────────────────────────────────────────
# Set these as App Settings in Azure (not needed locally — file:// fallback used)
SP_DOCS_BASE  = os.environ.get("SP_DOCS_BASE", "")   # e.g. https://bmgf.sharepoint.com/sites/Insight/StrategyDocuments/
SP_AMB45_BASE = os.environ.get("SP_AMB45_BASE", "")  # e.g. https://bmgf.sharepoint.com/sites/uspcentral/Public Documents/Ambition 2045 - shared materials/

LOCAL_DOCS_BASE  = "C:/Users/callanco/OneDrive - Gates Foundation/Insight - Strategy Documents/"
LOCAL_AMB45_BASE = "C:/Users/callanco/OneDrive - Gates Foundation/US Program - Ambition 2045 - shared materials/"

def to_url(path: str) -> str:
    """Return a SharePoint URL when deployed, or a local file:// URL for dev."""
    p = path.replace("\\", "/")
    if SP_DOCS_BASE and p.startswith(LOCAL_DOCS_BASE):
        rel = p[len(LOCAL_DOCS_BASE):]
        return SP_DOCS_BASE.rstrip("/") + "/" + quote(rel, safe="/") + "?web=1"
    if SP_AMB45_BASE and p.startswith(LOCAL_AMB45_BASE):
        rel = p[len(LOCAL_AMB45_BASE):]
        return SP_AMB45_BASE.rstrip("/") + "/" + quote(rel, safe="/") + "?web=1"
    return "file:///" + p  # local dev fallback

# ── Load index ────────────────────────────────────────────────────────────────
with open(INDEX_FILE, encoding="utf-8") as f:
    INDEX = json.load(f)["files"]

# ── Load skills reference ─────────────────────────────────────────────────────
with open(SKILLS_FILE, encoding="utf-8") as f:
    SKILLS = f.read()

# ── Load extracted document text ──────────────────────────────────────────────
doc_texts: dict[str, str] = {}

def _load_docx_blocks(filepath: str) -> None:
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    delimiters = list(re.finditer(r"---\s*(.+?\.docx)\s*---", content))
    for i, m in enumerate(delimiters):
        fname = os.path.basename(m.group(1).strip())
        start = m.start()
        end   = delimiters[i + 1].start() if i + 1 < len(delimiters) else len(content)
        doc_texts[fname] = content[start:end]

def _load_pdf_blocks(filepath: str) -> None:
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    delimiters = list(re.finditer(r"FILE:\s*(.+)", content))
    for i, m in enumerate(delimiters):
        fname = os.path.basename(m.group(1).strip())
        start = m.start()
        end   = delimiters[i + 1].start() if i + 1 < len(delimiters) else len(content)
        doc_texts[fname] = content[start:end]

if os.path.exists(EXTRACTED):
    _load_docx_blocks(EXTRACTED)
if os.path.exists(AMB45_EXT):
    _load_pdf_blocks(AMB45_EXT)

print(f"Loaded {len(INDEX)} indexed docs | {len(doc_texts)} with extracted text")

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── Retrieval ─────────────────────────────────────────────────────────────────
SKIP_TYPES = {"appendix", "table-of-contents", "acronym-list", "participant-bios", "org-chart"}

def _score(doc: dict, query_lower: str, tokens: list[str], mode: str) -> int:
    if doc["doc_type"] in SKIP_TYPES:
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

    if doc["filename"] in doc_texts:
        score += 1

    return score

def retrieve(query: str, mode: str, top_n: int = 5) -> list[dict]:
    q    = query.lower()
    toks = re.findall(r"\b\w{4,}\b", q)
    scored = sorted(
        ((s, d) for d in INDEX if (s := _score(d, q, toks, mode)) > 0),
        key=lambda x: -x[0],
    )
    return [d for _, d in scored[:top_n]]

# ── Chat endpoint ─────────────────────────────────────────────────────────────
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
        "explain whether they're correct and why, then ask if they'd like another question. "
        "Draw questions from the retrieved documents and the strategy knowledge base."
    ),
}

class ChatRequest(BaseModel):
    message: str
    mode:    str           # 'history' | 'amb45' | 'quiz'
    history: list = []

@app.post("/chat")
async def chat(req: ChatRequest):
    docs = retrieve(req.message, req.mode)

    context_parts = []
    sources = []
    for doc in docs:
        raw = doc_texts.get(doc["filename"], "")
        if raw:
            body = "\n".join(raw.split("\n")[1:]).strip()[:3000]
            year = str(doc["session_year"]) if doc["session_year"] else "undated"
            context_parts.append(
                f"[{doc['filename']} | {year} | {', '.join(doc['strategy_areas'])}]\n{body}"
            )
        sources.append({
            "filename": doc["filename"],
            "url":      to_url(doc["path"]),
            "year":     doc["session_year"],
            "topic":    doc["meeting_topic"],
            "areas":    doc["strategy_areas"],
            "doc_type": doc["doc_type"],
        })

    context_text = "\n\n---\n\n".join(context_parts) or "No extracted text available for the retrieved documents."

    system = f"""You are StrateGPT, an AI assistant for Gates Foundation U.S. Program (USP) strategy. \
You help colleagues navigate USP strategy documents and understand key concepts.

## USP Strategy Knowledge Base
{SKILLS}

## Retrieved Documents (most relevant to this query)
{context_text}

## Mode Instructions
{MODE_INSTRUCTIONS.get(req.mode, MODE_INSTRUCTIONS["history"])}

Cite documents by name and year when possible. Acknowledge uncertainty rather than speculating.

Formatting rules:
- Use **Bold text** for all section headers — do NOT use ## markdown headers
- Separate distinct concepts or thoughts with a blank line
- Do NOT use horizontal rules (---) or table/pipe syntax (|---|)
- Use plain bullet points (- item) for lists"""

    api_messages = []
    for h in req.history[-6:]:
        role    = "assistant" if h.get("role") == "ai" else "user"
        content = h.get("content", "")
        if content:
            api_messages.append({"role": role, "content": content})
    api_messages.append({"role": "user", "content": req.message})

    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=api_messages,
    )

    return {"response": result.content[0].text, "sources": sources}

@app.get("/health")
def health():
    return {
        "status":         "ok",
        "docs_indexed":   len(INDEX),
        "docs_with_text": len(doc_texts),
    }

# ── Serve frontend ────────────────────────────────────────────────────────────
@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(BASE, "index.html"))
