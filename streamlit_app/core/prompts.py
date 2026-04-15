"""
prompts.py — system prompt construction and streaming helper.
"""

MODE_INSTRUCTIONS: dict[str, str] = {
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
        "You are in Quiz Mode. Generate a single multiple-choice question (options A–D) that tests "
        "understanding of USP strategy concepts. Present only one question. After the user answers, "
        "tell them whether they are correct, explain why, then ask if they'd like another question. "
        "Draw questions from the retrieved documents and the strategy knowledge base."
    ),
    "synthesis": (
        "The user wants a cross-strategy synthesis. Draw explicitly on documents from EACH of the "
        "selected strategy areas. Identify shared themes, divergences, and how the strategies "
        "complement or create tensions with each other. Be specific about which insights come "
        "from which area and which documents."
    ),
}

FORMATTING_RULES = (
    "Formatting rules:\n"
    "- Use **Bold text** for all section headers — do NOT use ## markdown headers\n"
    "- Separate distinct concepts with a blank line\n"
    "- Use plain bullet points (- item) for lists\n"
    "- Do NOT use horizontal rules (---) or markdown tables\n"
    "- Cite documents by name and year when possible\n"
    "- Acknowledge uncertainty rather than speculating"
)


def build_system(mode: str, docs: list, doc_texts: dict, skills: str) -> str:
    parts = []
    for doc in docs:
        raw = doc_texts.get(doc["filename"], "")
        if raw:
            body = "\n".join(raw.split("\n")[1:]).strip()[:3000]
            year = str(doc["session_year"]) if doc["session_year"] else "undated"
            parts.append(
                f"[{doc['filename']} | {year} | {', '.join(doc['strategy_areas'])}]\n{body}"
            )
    context = "\n\n---\n\n".join(parts) or "No extracted text available for retrieved documents."

    instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["history"])

    return (
        "You are StrateGPT, an AI assistant for Gates Foundation U.S. Program (USP) strategy. "
        "You help colleagues navigate USP strategy documents and understand key concepts.\n\n"
        f"## USP Strategy Knowledge Base\n{skills}\n\n"
        f"## Retrieved Documents (most relevant to this query)\n{context}\n\n"
        f"## Mode Instructions\n{instruction}\n\n"
        f"{FORMATTING_RULES}"
    )


def build_api_messages(history: list, message: str) -> list[dict]:
    """Convert session history to Anthropic API message format."""
    api_msgs = []
    for h in history[-6:]:
        role    = "assistant" if h["role"] == "ai" else "user"
        content = h.get("content", "")
        if content:
            api_msgs.append({"role": role, "content": content})
    api_msgs.append({"role": "user", "content": message})
    return api_msgs


def stream_response(client, system: str, history: list, message: str):
    """Generator that yields text chunks from the Claude API."""
    api_msgs = build_api_messages(history, message)
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=api_msgs,
    ) as stream:
        yield from stream.text_stream
