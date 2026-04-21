"""
prompts.py — system prompt construction and streaming helpers.
"""

MODE_INSTRUCTIONS: dict[str, str] = {
    "history": (
        "Answer questions about U.S. Program strategy history (2019 to present). "
        "Draw on retrieved documents for specific, grounded answers. "
        "Reference document names and years. Highlight how strategies evolved over time."
    ),
    "amb45": (
        "Help the user understand Ambition 2045 and its connections to historical USP strategies. "
        "Reference specific legacy programs and how past investments laid groundwork for Amb'45 priorities. "
        "Be concrete about which priorities map to which legacy strategy areas."
    ),
    "quiz": (
        "You are a quiz bot testing knowledge of U.S. Program strategy. "
        "Generate a single multiple-choice question. "
        "You MUST format questions using EXACTLY this structure — no other format:\n\n"
        "<question text>\n\n"
        "<<OPTIONS>>\n"
        "A: <option text>\n"
        "B: <option text>\n"
        "C: <option text>\n"
        "D: <option text>\n"
        "<<END_OPTIONS>>\n\n"
        "When the user answers, respond with plain text only: confirm correct/incorrect, "
        "explain the right answer with citations, then ask if they want another question. "
        "Do NOT include <<OPTIONS>> tags when explaining an answer. "
        "Do NOT include citations when asking a question — only when explaining the answer."
    ),
    "sparknotes": (
        "Generate a concise Sparknotes-style primer on the selected USP strategy area. "
        "Structure your response with these sections:\n\n"
        "**Key Concepts & Frameworks** — the 4-6 most important ideas and vocabulary\n\n"
        "**Strategy Evolution** — how the strategy changed from 2019 to present, with years\n\n"
        "**Ambition 2045 Connection** — how this strategy connects to and supports Amb'45\n\n"
        "Write for someone cramming before a strategy meeting. Be specific and cite documents."
    ),
    "navigator": (
        "Analyze the selected USP strategy area across four dimensions. "
        "Use these exact section headers:\n\n"
        "**Strengths & Opportunities** — what is working and where momentum exists\n\n"
        "**Weaknesses & Risks** — gaps, tensions, or areas of vulnerability\n\n"
        "**Connections to Other Strategies** — how this strategy links to other USP strategy areas. "
        "Name other strategies explicitly using their full names "
        "(e.g. 'K-12 Education', 'Postsecondary Success', 'Pathways', 'Washington State Initiative', "
        "'USP Data', 'USPAC', 'Ambition 2045').\n\n"
        "**Anticipated Tradeoffs** — decisions or debates likely to surface in 2026\n\n"
        "Be specific and grounded in retrieved documents. Cite by name and year."
    ),
}

FORMATTING_RULES = (
    "Formatting rules:\n"
    "- Use **Bold** for all section headers\n"
    "- Use plain bullet points (- item) for lists\n"
    "- Separate distinct sections with a blank line\n"
    "- Cite documents by name and year when instructed\n"
    "- Acknowledge uncertainty rather than speculating"
)


def build_system(mode: str, docs: list, doc_texts: dict, skills: str) -> str:
    parts = []
    for doc in docs:
        raw = doc_texts.get(doc["filename"], "")
        if raw:
            body = "\n".join(raw.split("\n")[1:]).strip()[:3000]
            year = str(doc["session_year"]) if doc["session_year"] else "undated"
            parts.append(f"[{doc['filename']} | {year} | {', '.join(doc['strategy_areas'])}]\n{body}")
    context = "\n\n---\n\n".join(parts) or "No extracted text available for retrieved documents."
    instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["history"])

    return (
        "You are StrateGPT, an AI assistant for Gates Foundation U.S. Program (USP) strategy.\n\n"
        f"## USP Strategy Knowledge Base\n{skills}\n\n"
        f"## Retrieved Documents\n{context}\n\n"
        f"## Instructions\n{instruction}\n\n"
        f"{FORMATTING_RULES}"
    )


def stream_response(client, system: str, history: list, message: str):
    """Yield text chunks from Claude (streaming)."""
    api_msgs = _to_api_messages(history, message)
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=api_msgs,
    ) as stream:
        yield from stream.text_stream


def get_response(client, system: str, history: list, message: str, max_tokens: int = 1500) -> str:
    """Return full response text (non-streaming)."""
    api_msgs = _to_api_messages(history, message)
    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=api_msgs,
    )
    return result.content[0].text


def generate_suggestions(client, mode: str, skills: str) -> list[str]:
    """Generate 3-4 suggested questions for a given chat mode."""
    prompts = {
        "history": (
            "Generate exactly 4 short, compelling questions a Gates Foundation staff member "
            "might ask about U.S. Program strategy history (2019-2025). "
            "Span different strategy areas. Return only the questions, one per line, no numbering or bullets."
        ),
        "amb45": (
            "Generate exactly 4 short, compelling questions about Ambition 2045 "
            "and how it connects to USP strategy history. "
            "Return only the questions, one per line, no numbering or bullets."
        ),
    }
    if mode not in prompts:
        return []
    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=f"You are a knowledgeable assistant for Gates Foundation USP strategy.\n\n{skills[:4000]}",
        messages=[{"role": "user", "content": prompts[mode]}],
    )
    lines = [ln.strip() for ln in result.content[0].text.strip().splitlines() if ln.strip()]
    return lines[:4]


def _to_api_messages(history: list, message: str) -> list[dict]:
    api_msgs = []
    for h in history[-8:]:
        role    = "assistant" if h["role"] == "ai" else "user"
        content = h.get("content", "")
        if h.get("options"):
            opts = "\n".join(f"{k}: {v}" for k, v in h["options"].items())
            content = f"{content}\n\n<<OPTIONS>>\n{opts}\n<<END_OPTIONS>>"
        if content:
            api_msgs.append({"role": role, "content": content})
    api_msgs.append({"role": "user", "content": message})
    return api_msgs
