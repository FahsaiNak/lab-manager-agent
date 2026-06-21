"""Custom tools for the Knowledge Curator sub-agent (SPEC.md §2.2, §3).

The "wiki" here is a deliberately simple JSON index built from the synthetic
corpus in sandbox/corpus/ (see scripts/ingest_corpus.py) — keyword retrieval,
not embeddings/vector search, since the corpus is small and the rubric cares
about provenance discipline, not retrieval sophistication.
"""

import json
import os
import re

_APP_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.join(_APP_DIR, "..")
WIKI_INDEX_PATH = os.path.abspath(os.path.join(_PROJECT_ROOT, "wiki_index.json"))

_STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "to",
    "of",
    "in",
    "on",
    "for",
    "and",
    "or",
    "what",
    "how",
    "does",
    "do",
    "did",
    "this",
    "that",
    "it",
    "its",
    "with",
    "as",
    "at",
    "by",
    "from",
}


def _load_index() -> dict:
    if not os.path.exists(WIKI_INDEX_PATH):
        return {}
    with open(WIKI_INDEX_PATH) as f:
        return json.load(f)


def _save_index(index: dict) -> None:
    with open(WIKI_INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Splits a '---' delimited YAML-ish frontmatter block from the body.

    Only handles flat key: value pairs, which is all this corpus uses.
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    _blank, frontmatter_block, body = parts
    meta = {}
    for line in frontmatter_block.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.strip()


def _extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def ingest_doc(doc_path: str) -> dict:
    """Ingests a markdown document into the lab wiki index.

    Args:
        doc_path: Absolute path to the markdown document to ingest.

    Returns:
        dict with 'status', 'page_id', and 'title' for the ingested page.
        The page's provenance (source_path) is always the original doc_path.
    """
    with open(doc_path) as f:
        raw = f.read()
    meta, body = _parse_frontmatter(raw)

    page_id = os.path.splitext(os.path.basename(doc_path))[0]
    title = _extract_title(body, fallback=page_id)

    index = _load_index()
    index[page_id] = {
        "title": title,
        "type": meta.get("type", "unknown"),
        "status": meta.get("status", ""),
        "content": body,
        "source_path": doc_path,
    }
    _save_index(index)

    return {"status": "ingested", "page_id": page_id, "title": title}


def query_wiki(question: str) -> dict:
    """Searches the lab wiki index for content relevant to a question.

    Args:
        question: The user's question.

    Returns:
        dict with 'status' and 'matches'. Each match has 'page_id', 'title',
        'content', and 'source_path' for citation. Empty matches means the
        wiki has no relevant content — report that to the user rather than
        guessing an answer.
    """
    index = _load_index()
    terms = [
        w for w in re.findall(r"[a-z0-9]+", question.lower()) if w not in _STOPWORDS
    ]

    scored = []
    for page_id, page in index.items():
        haystack_words = re.findall(
            r"[a-z0-9]+", (page["title"] + " " + page["content"]).lower()
        )
        score = sum(haystack_words.count(term) for term in terms)
        if score > 0:
            scored.append((score, page_id, page))

    scored.sort(key=lambda x: x[0], reverse=True)
    matches = [
        {
            "page_id": page_id,
            "title": page["title"],
            "content": page["content"],
            "source_path": page["source_path"],
        }
        for _score, page_id, page in scored[:3]
    ]
    return {"status": "success", "matches": matches}
