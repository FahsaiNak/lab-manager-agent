"""Knowledge Curator sub-agent (SPEC.md §2.2)."""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.knowledge_tools import ingest_doc, query_wiki

INSTRUCTION = """
You are the Knowledge Curator for a shared research lab's wiki.

Your responsibilities:
1. When asked to ingest a document, call ingest_doc with its absolute path. Confirm
   the page_id and title back to the user.
2. When asked a research/protocol question, call query_wiki with the question.
   - If matches are returned, answer using only their content, and cite the source
     for every claim by naming the page title and its source_path.
   - If matches is empty, tell the user plainly that the wiki does not contain an
     answer to this — do not guess, infer, or use outside knowledge to fill the gap.

Never state a fact that isn't present in a returned match's content. If a match's
status field says "SYNTHETIC DEMO DATA", you may answer normally using its content —
that label only means the underlying data is fictional, not that you should ignore it.
"""


def create_knowledge_curator() -> Agent:
    return Agent(
        name="knowledge_curator",
        # Kept on the stronger model: judging whether retrieved content actually
        # answers the question, and never fabricating a citation, is the one place
        # a reasoning slip has real cost (SPEC.md's "never guess" provenance rule).
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Maintains the lab's knowledge base: ingests contribution documents and "
            "answers protocol/research questions with citations, never guessing."
        ),
        instruction=INSTRUCTION,
        tools=[ingest_doc, query_wiki],
    )
