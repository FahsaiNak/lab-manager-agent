"""Custom tools for the News Scout sub-agent (SPEC.md §2.3, §3).

search_papers reads a static synthetic feed (sandbox/news_feed.json) — this
demo never calls a real external search API. Per-paper digest dedup reuses
app.tools.post_to_slack's existing dedup_key mechanism (see news_scout.py),
keyed on each paper's url.
"""

import json
import os

_APP_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.join(_APP_DIR, "..")
NEWS_FEED_PATH = os.path.abspath(
    os.path.join(_PROJECT_ROOT, "sandbox", "news_feed.json")
)

LAB_INTEREST_TAGS = ["molecular dynamics", "HIV Env", "bnAb design"]


def search_papers(query_tags: list[str]) -> dict:
    """Searches the synthetic news feed for items matching any of the given tags.

    Args:
        query_tags: Lab interest tags to match against, e.g.
            ["molecular dynamics", "HIV Env", "bnAb design"].

    Returns:
        dict with 'status' and 'results'. Each result has id, title, source,
        url, snippet, and tags. A tag matches case-insensitively. Empty
        results means nothing in the feed matches today — report that rather
        than inventing a paper.
    """
    with open(NEWS_FEED_PATH) as f:
        feed = json.load(f)

    query_lower = {t.lower() for t in query_tags}
    results = [
        item
        for item in feed["items"]
        if query_lower & {t.lower() for t in item["tags"]}
    ]
    return {"status": "success", "results": results}
