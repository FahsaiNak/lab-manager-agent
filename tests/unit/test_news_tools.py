"""Unit tests for app/news_tools.py — no LLM calls.

Covers SPEC.md §5 News Scout eval cases 1-2: tag-matching retrieval and
negative filtering for unrelated items.
"""

import json

from app import news_tools


def _write_feed(path, items):
    path.write_text(json.dumps({"_comment": "test fixture", "items": items}))


def test_search_papers_matches_overlapping_tags(tmp_path, monkeypatch):
    feed_path = tmp_path / "news_feed.json"
    _write_feed(
        feed_path,
        [
            {
                "id": "p1",
                "title": "Matching Paper",
                "source": "Demo Source",
                "url": "https://example.invalid/p1",
                "snippet": "...",
                "tags": ["HIV Env", "bnAb design"],
            }
        ],
    )
    monkeypatch.setattr(news_tools, "NEWS_FEED_PATH", str(feed_path))

    result = news_tools.search_papers(["molecular dynamics", "HIV Env"])

    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "p1"


def test_search_papers_excludes_unrelated_items(tmp_path, monkeypatch):
    feed_path = tmp_path / "news_feed.json"
    _write_feed(
        feed_path,
        [
            {
                "id": "p2",
                "title": "Unrelated Paper",
                "source": "Demo Source",
                "url": "https://example.invalid/p2",
                "snippet": "...",
                "tags": ["membrane proteins"],
            }
        ],
    )
    monkeypatch.setattr(news_tools, "NEWS_FEED_PATH", str(feed_path))

    result = news_tools.search_papers(["molecular dynamics", "HIV Env", "bnAb design"])

    assert result["status"] == "success"
    assert result["results"] == []


def test_search_papers_is_case_insensitive(tmp_path, monkeypatch):
    feed_path = tmp_path / "news_feed.json"
    _write_feed(
        feed_path,
        [
            {
                "id": "p3",
                "title": "Case Test Paper",
                "source": "Demo Source",
                "url": "https://example.invalid/p3",
                "snippet": "...",
                "tags": ["hiv env"],
            }
        ],
    )
    monkeypatch.setattr(news_tools, "NEWS_FEED_PATH", str(feed_path))

    result = news_tools.search_papers(["HIV Env"])

    assert len(result["results"]) == 1
