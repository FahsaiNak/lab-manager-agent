# Lab Manager Agent — Kaggle Writeup Draft

> Track: **Concierge Agents**
> This is a draft of the Kaggle Writeup content — copy/adapt into the Kaggle submission
> form. Structured to map directly onto the rubric: Pitch (Problem/Solution/Value, 30 pts)
> and Implementation (Architecture/Code, 70 pts).

---

## Problem

Research labs accumulate shared administrative burden that no single person owns:

- **Storage** — shared cluster/cloud space fills with stale runs nobody archives.
  Occasionally someone outside the lab's authorized group writes into lab space they
  shouldn't have access to, and nobody notices until a quota alert fires or, worse,
  never.
- **Knowledge** — protocols, results, and findings live scattered across docs, Slack
  threads, and READMEs. New members — and existing ones — re-ask questions that were
  already answered somewhere, because there's no single place to look.
- **Shared awareness** — papers and news relevant to the lab's research interests
  surface unevenly. Whoever happens to see them shares them; often nobody does.

These are *concierge-style* problems: individually low-stakes, but a constant
low-grade tax on a lab's time — usually absorbed informally by whichever grad student
or postdoc happens to be the most organized.

## Solution

**Lab Manager Agent** is a multi-agent system built with Google's Agent Development
Kit (ADK) that takes over this work:

```
lab_manager_orchestrator (root agent)
├── Storage Steward    — scans lab storage, proposes archiving stale work,
│                        detects and alerts on unauthorized writes
├── Knowledge Curator   — ingests lab documents into a wiki, answers protocol/
│                        research questions with citations (never guesses)
└── News Scout          — searches for papers matching the lab's interest tags
                          and posts a digest to Slack
```

A single orchestrator agent routes every incoming request — a direct question, a
Slack mention, or a scheduled trigger — to exactly one sub-agent, using ADK's
LLM-driven `transfer_to_agent` delegation. Each sub-agent owns its own deterministic
tools and never silently invokes another agent's tools.

**Security by design.** The Storage Steward can *propose* an archive plan freely, but
the system enforces — at the code layer, not just by prompting — that no archive
plan can be executed without an explicit human confirmation. This is implemented as
an ADK `before_tool_callback` that inspects every tool call before it runs and blocks
`execute_archive_plan` outright unless `confirm=True` is present. We verified this
guardrail live: telling the agent to "execute it right away" in the same breath as
the request still produced a stop-and-ask response, and a deliberate adversarial
prompt asking the model to call the tool with `confirm=False` was intercepted by the
callback before the tool body ever ran.

**Demo environment.** Everything runs against a sandboxed, synthetic environment —
a fake cluster filesystem with planted stale directories and one unauthorized write,
a synthetic corpus of lab documents (protocols, results, paper notes), and a synthetic
paper feed. No real lab credentials, storage, or Slack workspace are used anywhere in
this repo or demo — all fixture content is explicitly labeled as fictional.

## Value

- **Storage Steward** turns an ignored quota problem into a proactive, low-noise
  recommend-and-alert system — it never deletes anything on its own, and anomaly
  alerts are deduplicated so the channel isn't spammed by the same finding twice.
- **Knowledge Curator** gives a lab a queryable institutional memory with provenance:
  every answer cites the document it came from, and the agent explicitly says "not in
  the wiki" rather than inventing a plausible-sounding but wrong answer — critical for
  a research setting where a wrong protocol detail has real cost.
- **News Scout** removes the "did anyone see this paper?" coordination tax — every
  lab member gets the same digest, automatically, with no duplicate posts across runs.
- The pattern generalizes beyond one lab: any small group sharing storage, an
  evolving knowledge base, and a topical interest list (a research group, an open
  source project, a small team) faces the same three problems.

## Implementation

- **Stack:** Google ADK 2.0 (Python), Gemini (`gemini-flash-latest`), built and run
  via `agents-cli` / Antigravity IDE, authenticated against a Google AI Studio API key.
- **ADK concepts demonstrated (≥3):**
  1. **Multi-agent orchestration** — `Agent(sub_agents=[...])` with LLM-driven
     `transfer_to_agent`; the orchestrator holds no tools of its own.
  2. **Custom function tools** — 8 deterministic, side-effect-bounded tools across
     the three sub-agents (filesystem scanning, anomaly detection, archive proposal/
     execution, Slack posting with dedup/rate-limiting, wiki ingest/query, paper
     search).
  3. **Security guardrail via `before_tool_callback`** — blocks destructive tool
     calls without explicit human confirmation; verified live against an adversarial
     bypass attempt.
  4. **Eval-driven development** — every sub-agent was built against eval cases
     written *before* the code (`SPEC.md` §5), then verified with live `agents-cli
     run` smoke tests plus a deterministic `pytest` suite (16 tests) for all
     non-LLM tool/guardrail logic.
- **Verification:** all 5 Storage Steward eval cases, all 3 Knowledge Curator eval
  cases, all 3 News Scout eval cases, and all 3 orchestrator routing eval cases passed
  against live Gemini calls (not just unit tests) — see `SPEC.md` §5 for the full list
  and the project's test history for evidence.

## Links

- GitHub repo: https://github.com/FahsaiNak/lab-manager-agent
- Demo video: _\<add video URL before submitting\>_
