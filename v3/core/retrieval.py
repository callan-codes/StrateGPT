"""
retrieval.py — document scoring and retrieval.
"""
import re

SKIP_TYPES = {
    "appendix", "table-of-contents", "acronym-list",
    "participant-bios", "org-chart",
}


def _score(doc, query_lower, tokens, mode, area_filter, doc_texts):
    if doc["doc_type"] in SKIP_TYPES:
        return 0
    if area_filter and not any(a in doc["strategy_areas"] for a in area_filter):
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


def retrieve(query, mode, index, doc_texts, top_n=5, area_filter=None):
    q    = query.lower()
    toks = re.findall(r"\b\w{4,}\b", q)
    scored = sorted(
        ((s, d) for d in index if (s := _score(d, q, toks, mode, area_filter, doc_texts)) > 0),
        key=lambda x: -x[0],
    )
    return [d for _, d in scored[:top_n]]
