"""Unit tests for app/knowledge_tools.py — no LLM calls.

Covers SPEC.md §5 Knowledge Curator eval cases 1-3: answer-with-citation
retrieval, "not in the wiki" for no match, and ingest provenance.
"""

from app import knowledge_tools


def _write_doc(path, type_, title, body_text):
    path.write_text(
        f"---\ntype: {type_}\nstatus: SYNTHETIC DEMO DATA\n---\n\n# {title}\n\n{body_text}\n"
    )


def test_ingest_doc_extracts_title_and_provenance(tmp_path, monkeypatch):
    index_path = tmp_path / "wiki_index.json"
    monkeypatch.setattr(knowledge_tools, "WIKI_INDEX_PATH", str(index_path))

    doc_path = tmp_path / "protocol-x.md"
    _write_doc(doc_path, "protocol", "Protocol X", "Step one. Step two.")

    result = knowledge_tools.ingest_doc(str(doc_path))

    assert result["status"] == "ingested"
    assert result["page_id"] == "protocol-x"
    assert result["title"] == "Protocol X"

    index = knowledge_tools._load_index()
    assert index["protocol-x"]["source_path"] == str(doc_path)
    assert index["protocol-x"]["type"] == "protocol"


def test_query_wiki_returns_match_with_citation(tmp_path, monkeypatch):
    index_path = tmp_path / "wiki_index.json"
    monkeypatch.setattr(knowledge_tools, "WIKI_INDEX_PATH", str(index_path))

    doc_path = tmp_path / "equilibration.md"
    _write_doc(
        doc_path,
        "protocol",
        "Equilibration Protocol",
        "Run NVT equilibration for 100 ps at 310 K before NPT.",
    )
    knowledge_tools.ingest_doc(str(doc_path))

    result = knowledge_tools.query_wiki("How long should NVT equilibration run?")

    assert result["status"] == "success"
    assert len(result["matches"]) == 1
    assert result["matches"][0]["source_path"] == str(doc_path)
    assert "100 ps" in result["matches"][0]["content"]


def test_query_wiki_no_match_returns_empty(tmp_path, monkeypatch):
    index_path = tmp_path / "wiki_index.json"
    monkeypatch.setattr(knowledge_tools, "WIKI_INDEX_PATH", str(index_path))

    doc_path = tmp_path / "unrelated.md"
    _write_doc(
        doc_path, "protocol", "Unrelated Protocol", "Completely different topic."
    )
    knowledge_tools.ingest_doc(str(doc_path))

    result = knowledge_tools.query_wiki("What is the boiling point of helium?")

    assert result["status"] == "success"
    assert result["matches"] == []


def test_query_wiki_does_not_substring_match_inside_other_words(tmp_path, monkeypatch):
    index_path = tmp_path / "wiki_index.json"
    monkeypatch.setattr(knowledge_tools, "WIKI_INDEX_PATH", str(index_path))

    doc_path = tmp_path / "unrelated.md"
    _write_doc(
        doc_path,
        "protocol",
        "Unrelated Protocol",
        "This fixture is used here only as demo content.",
    )
    knowledge_tools.ingest_doc(str(doc_path))

    # "use" is a substring of "used" but not a real word match for this doc.
    result = knowledge_tools.query_wiki(
        "What buffer recipe does the lab use for ELISA assays?"
    )

    assert result["status"] == "success"
    assert result["matches"] == []
