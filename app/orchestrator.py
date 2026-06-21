"""Lab Manager orchestrator (SPEC.md Architecture diagram, §5 Orchestrator evals).

Routes every request to exactly one sub-agent via ADK's LLM-driven
transfer_to_agent — the orchestrator holds no tools of its own.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.sub_agents.knowledge_curator import create_knowledge_curator
from app.sub_agents.news_scout import create_news_scout
from app.sub_agents.storage_steward import create_storage_steward

INSTRUCTION = """
You are the orchestrator for a shared research lab's management system. You hold no
tools yourself — you must delegate every request to exactly one of these sub-agents:

- storage_steward: filesystem scans, stale/inactive directory reports, archive
  proposals and execution, unauthorized-write or access-anomaly detection and alerts.
- knowledge_curator: ingesting lab documents into the wiki, and answering research or
  lab-protocol questions from the wiki.
- news_scout: searching for papers/news matching the lab's interest tags and posting a
  digest to Slack — this includes generic "run the digest" or scheduled-trigger style
  requests that carry no specific question.

Pick the single most relevant sub-agent and transfer to it. Do not try to answer
storage, wiki, or news questions yourself, and do not transfer to more than one
sub-agent for a single request.
"""


def create_orchestrator() -> Agent:
    return Agent(
        name="lab_manager_orchestrator",
        # Lite model: a 3-way routing decision, low reasoning risk.
        model=Gemini(
            model="gemini-3.1-flash-lite",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Routes lab management requests to the Storage Steward, Knowledge "
            "Curator, or News Scout sub-agent."
        ),
        instruction=INSTRUCTION,
        sub_agents=[
            create_storage_steward(),
            create_knowledge_curator(),
            create_news_scout(),
        ],
    )
