# Lab Manager Agent — Spec

> Capstone: Kaggle "AI Agents: Intensive Vibe Coding Capstone Project"
> Track: Concierge Agents
> Stack: Google ADK 2.0, Gemini (gemini-3.5-flash for Knowledge Curator,
> gemini-3.1-flash-lite for the orchestrator/Storage Steward/News Scout),
> built/run via Antigravity IDE
> Deadline: 2026-07-06 23:59 PT

This spec is written before any agent code. Build order follows this document.
Do not add tools, agents, or behaviors not listed here without updating this file first.

---

## 1. Problem

Research labs accumulate shared state that nobody owns full-time:

- **Storage**: shared cluster/cloud space fills with stale runs nobody archives; occasionally
  someone outside the lab's authorized group writes into lab space they shouldn't have access to,
  and nobody notices until disk quota alerts fire.
- **Knowledge**: protocols, results, and findings live in scattered docs/Slack threads/READMEs.
  New members and even existing members re-ask questions that were already answered somewhere.
- **Shared awareness**: papers and news relevant to the lab's interests surface unevenly —
  whoever happens to see them shares them, or nobody does.

These are concierge-style problems: ongoing, low-stakes-per-instance, high-cumulative-cost
administrative burden for a defined group of people (the lab).

## 2. Solution — Agent Architecture

```
Lab Manager (orchestrator agent)
├── Storage Steward    (sub-agent)
├── Knowledge Curator   (sub-agent)
└── News Scout          (sub-agent)
```

The orchestrator routes incoming requests (Slack mentions, scheduled triggers, or direct
queries) to the correct sub-agent and holds shared session state (lab member list, interest
tags, last-run timestamps per sub-agent).

**Demo environment:** all three sub-agents run against a **sandboxed synthetic environment**:
a fake cluster-style filesystem tree, a synthetic corpus of "lab contribution" docs, and a
sandbox Slack workspace/webhook. No real lab credentials, storage, or Slack workspace are used
in the public repo or demo.

### 2.1 Storage Steward

Scans the synthetic filesystem (modeled on HPC cluster conventions: per-user/per-project dirs,
mtimes, group ownership, quota files) and:

- Flags directories inactive beyond a configurable threshold (default 90 days, by mtime) as
  archive candidates.
- Proposes (never silently executes) archive/cleanup actions — output is a plan, not an action,
  until confirmed.
- Detects anomalous access: writes appearing under a project directory from a user not in that
  project's authorized group list (the "out-source people try to evade" case from the original
  ask) — this is a static authorized-group-list check against synthetic file ownership metadata,
  not real intrusion detection.
- Alerts via the Slack tool when an anomaly is detected or when an archive plan is ready for
  review.

**Explicitly out of scope:** real SLURM integration, real quota enforcement, actually deleting
files. This is a recommend-and-alert agent, not an autonomous file-deletion agent — destructive
actions require human confirmation (see §4 Guardrails).

### 2.2 Knowledge Curator

Ingests a synthetic corpus of "lab contribution" documents (mocked protocols, results notes,
paper summaries) into a small wiki/knowledge base and answers Q&A against it.

Reuses the provenance + typed-edge pattern already proven out in the Sprenger Lab BioWiki
(`research-wiki` project): every wiki page tracks its source doc, and claims are never invented
— if the corpus doesn't contain an answer, the agent says so rather than guessing.

**Explicitly out of scope:** ingesting real lab Drive/GitHub data for this capstone demo (privacy/
scope) — the corpus is synthetic but structurally realistic (protocol docs, results summaries,
paper notes).

### 2.3 News Scout

On a scheduled trigger (or on-demand), searches for new papers/news matching a configured list
of lab interest tags (e.g., for an MD-based lab: "molecular dynamics," "HIV Env," "bnAb design")
and posts a digest to the sandbox Slack thread: title, source, one-line relevance note.

**Explicitly out of scope:** real-time monitoring (cron-like scheduled or manually triggered
only), filtering for novelty beyond "not already in the digest history."

## 3. Tool Contracts

| Tool | Used by | Input | Output |
|---|---|---|---|
| `scan_filesystem(root_path)` | Storage Steward | path | list of `{path, owner, group, mtime, size}` |
| `read_authorized_groups()` | Storage Steward | — | `{project: [authorized_users]}` |
| `propose_archive_plan(stale_dirs)` | Storage Steward | list of dirs | plan object (not executed) |
| `post_to_slack(channel, message)` | Storage Steward, News Scout | channel, text | post confirmation |
| `ingest_doc(doc_path)` | Knowledge Curator | path | wiki page written |
| `query_wiki(question)` | Knowledge Curator | text | answer + cited source page(s) |
| `search_papers(query_tags)` | News Scout | tags | list of `{title, source, url, snippet}` |

All tools are deterministic, side-effect-bounded functions — no tool silently calls another
tool. Destructive or external-facing tools (`propose_archive_plan` executing, `post_to_slack`)
are gated by the guardrail callback in §4.

## 4. Guardrails (Security Feature #1)

Implemented as an ADK `before_tool_callback`:

- Any tool call that would **modify or delete files** is blocked unless a prior explicit
  confirmation step (`confirm: true` in the session state, set only by a human-in-the-loop
  response) is present. The agent always proposes before acting.
- Any `post_to_slack` call is rate-limited (max N posts per sub-agent per run) to prevent
  noisy/duplicate alerts.
- Anomaly alerts (unauthorized-write detection) bypass the rate limit but are deduplicated
  against a "already alerted on this path" log so the same anomaly doesn't spam the channel.

## 5. Eval Cases (write before building each sub-agent)

### Storage Steward
1. Given a synthetic tree with one dir untouched for 120 days → flagged as archive candidate.
2. Given a dir touched 10 days ago → NOT flagged.
3. Given a file written by a user not in that project's authorized group → anomaly alert fires.
4. Given the same anomaly on a second scan with no new activity → no duplicate alert.
5. Attempting to execute an archive/delete action without confirmation → blocked by guardrail.

### Knowledge Curator
1. Question with a clear answer in the synthetic corpus → correct answer + correct citation.
2. Question with no answer in the corpus → agent says "not in the wiki," does not guess.
3. Ingesting a new doc → creates a wiki page with provenance back to the source doc.

### News Scout
1. Given interest tags matching a planted synthetic "new paper" → appears in the digest.
2. Given a paper already posted in a prior digest → not repeated.
3. Digest message posted to Slack matches the expected format (title/source/relevance note).

### Orchestrator (end-to-end)
1. A storage-related request routes to Storage Steward, not the other two sub-agents.
2. A protocol question routes to Knowledge Curator.
3. A scheduled trigger with no user message correctly invokes News Scout.

## 6. Cut Lines (if time runs short before 2026-07-06)

1. Drop News Scout entirely — Storage Steward + Knowledge Curator + guardrails alone satisfy
   the "≥3 concepts" rubric requirement (multi-agent, custom tools, security callback).
2. If still short: reduce Knowledge Curator to a single ingest + single Q&A demo rather than a
   full corpus.
3. Never cut: the guardrail callback (it's the cheapest, highest-signal "security feature" for
   the rubric) and the eval cases (needed to credibly claim the implementation works in the
   Writeup).

## 7. Deliverables Checklist

- [ ] Kaggle Writeup: Problem / Solution / Value (target the 30-pt Pitch rubric explicitly)
- [ ] Public GitHub repo (this project)
- [ ] Video demo showing all built sub-agents + at least one guardrail block in action
- [ ] Project link submitted to Concierge Agents track before 2026-07-06 23:59 PT
