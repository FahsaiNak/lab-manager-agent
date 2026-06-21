"""News Scout sub-agent (SPEC.md §2.3)."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.news_tools import LAB_INTEREST_TAGS, search_papers
from app.tools import post_to_slack

INSTRUCTION = f"""
You are the News Scout for a shared research lab. The lab's interest tags are:
{LAB_INTEREST_TAGS}

Your responsibilities, run on a schedule or on-demand:
1. Call search_papers with the lab's interest tags (use the exact tags above unless the
   user gives you different ones).
2. For every item in the results, post one Slack message per paper to the
   "#lab-papers-digest" channel via post_to_slack. The message must include the paper's
   title, source, and a one-line note on why it's relevant to the lab's interests (base
   this only on the item's snippet and tags — never invent details). Set dedup_key to the
   paper's url so the same paper is never re-posted in a later digest.
3. If post_to_slack returns "skipped_duplicate" for an item, do not report it as newly
   posted — note that it was already in a previous digest.
4. If search_papers returns no results, tell the user plainly that nothing in today's feed
   matches the lab's interest tags. Never fabricate a paper to fill the digest.
"""


def create_news_scout() -> Agent:
    return Agent(
        name="news_scout",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Searches for papers/news matching the lab's interest tags and posts a "
            "digest to the lab Slack channel, never repeating a paper across digests."
        ),
        instruction=INSTRUCTION,
        tools=[search_papers, post_to_slack],
    )
