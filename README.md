# Lab Manager Agent

A multi-agent system that handles the recurring administrative work of a shared research
lab: archiving stale storage and flagging unauthorized access, answering protocol/research
questions from a lab knowledge base, and keeping the lab updated on papers matching its
shared interests. Built for the Kaggle "AI Agents: Intensive Vibe Coding" capstone
(Concierge Agents track) with Google's Agent Development Kit (ADK).

See [`SPEC.md`](SPEC.md) for the full design spec (problem, architecture, tool contracts,
guardrails, eval cases) — that file is the source of truth this project was built against.

## Demo video

[![Lab Manager Agent demo](https://img.youtube.com/vi/nW2QL3GNiBs/maxresdefault.jpg)](https://youtu.be/nW2QL3GNiBs)

## Kaggle submission

[Lab Manager Agent — Kaggle Writeup](https://kaggle.com/competitions/vibecoding-agents-capstone-project/writeups/new-writeup-1782088031644)

## Architecture

```
lab_manager_orchestrator (root agent)
├── storage_steward      — filesystem scans, archive proposals, anomaly alerts
├── knowledge_curator    — wiki ingest + cited Q&A over lab documents
└── news_scout           — interest-tag paper search + Slack digest
```

The orchestrator holds no tools itself — it routes every request to exactly one
sub-agent via ADK's `sub_agents` + `transfer_to_agent` mechanism.

**Demo environment:** everything runs against a sandboxed, synthetic environment —
a fake cluster filesystem (`sandbox/cluster_fs/`, generated at runtime), a synthetic
lab-document corpus (`sandbox/corpus/`), and a mock Slack post log
(`slack_mock_log.json`). No real lab data, credentials, or Slack workspace are used.

## Key ADK concepts demonstrated

1. **Multi-agent orchestration** — `Agent(sub_agents=[...])` with LLM-driven
   `transfer_to_agent` routing (`app/orchestrator.py`).
2. **Custom function tools** — 8 deterministic tools across the three sub-agents
   (`app/tools.py`, `app/knowledge_tools.py`, `app/news_tools.py`).
3. **Security guardrail via `before_tool_callback`** — blocks any destructive
   archive execution unless a human has explicitly confirmed it (`app/guardrails.py`).
4. **Eval-driven development** — every sub-agent and the orchestrator's routing were
   built against eval cases defined in `SPEC.md` §5 *before* being verified with live
   `agents-cli run` smoke tests.
5. **Cost-tiered multi-model routing** — the orchestrator, Storage Steward, and News
   Scout run on `gemini-3.1-flash-lite` (mechanical tool orchestration over
   deterministic logic, low reasoning risk); Knowledge Curator stays on
   `gemini-3.5-flash` because judging whether retrieved wiki content actually
   answers the question — and never fabricating a citation — is the one place a
   reasoning slip has real cost.

## Setup

```bash
uv sync
```

Add a Gemini API key (Google AI Studio) to `app/.env`:

```
GOOGLE_API_KEY="your-key-here"
```

Generate the sandbox fixtures (synthetic filesystem + wiki corpus):

```bash
uv run python scripts/generate_sandbox.py
uv run python scripts/ingest_corpus.py
```

## Running

```bash
agents-cli run "Scan the lab filesystem and tell me which directories are stale and should be archived."
agents-cli run "What temperature and duration should I use for NVT equilibration?"
agents-cli run "[Scheduled trigger] Run the daily news digest."
agents-cli playground   # interactive web UI
```

## Testing

```bash
uv run pytest tests/unit/ -q   # deterministic tool/guardrail logic — no LLM calls
agents-cli eval generate && agents-cli eval grade   # LLM behavior evals
```

## Project layout

```
app/
├── agent.py               # App entrypoint — root_agent = orchestrator
├── orchestrator.py        # Routes requests to sub-agents
├── guardrails.py          # before_tool_callback: blocks unconfirmed archive execution
├── tools.py                # Storage Steward tools
├── knowledge_tools.py      # Knowledge Curator tools
├── news_tools.py           # News Scout tools
└── sub_agents/             # storage_steward.py, knowledge_curator.py, news_scout.py
sandbox/                    # synthetic fixtures (cluster_fs is gitignored/generated)
scripts/                     # generate_sandbox.py, ingest_corpus.py
tests/unit/                  # deterministic tests for tools.py / guardrails.py
SPEC.md                      # design spec — read this first
```
