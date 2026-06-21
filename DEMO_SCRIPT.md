# Demo Video Script

Target length: ~4-5 minutes. Every command below has already been verified live
against real Gemini calls — this is a recording script, not untested material.

**Before recording:**

```bash
rm -f slack_mock_log.json wiki_index.json
uv run python scripts/generate_sandbox.py
uv run python scripts/ingest_corpus.py
```

---

## 1. Intro (15s, talking head or title card)

> "Lab Manager Agent — a multi-agent system built with Google's ADK that handles
> three recurring admin problems in a shared research lab: stale storage, scattered
> knowledge, and missed papers. Everything you'll see runs against a sandboxed,
> synthetic environment — no real lab data."

Show the architecture diagram from `README.md` on screen.

## 2. Storage Steward — stale-file detection (30s)

```bash
agents-cli run "Scan the lab filesystem and tell me which directories are stale and should be archived."
```

Narrate while it runs: "The orchestrator routes this to the Storage Steward, which
scans the synthetic cluster filesystem and flags anything older than 90 days."

Point out in the output: the `transfer_to_agent` call (multi-agent routing), the two
correctly-flagged stale files, the two correctly-excluded fresh ones.

## 3. Storage Steward — unauthorized write alert (30s)

```bash
agents-cli run "Check the lab filesystem for any unauthorized writes and alert the lab Slack if you find any."
```

Narrate: "There's a planted anomaly — a file written by `guest_user`, who isn't in
`combatrl`'s authorized group. The agent detects it and posts a Slack alert."

```bash
cat slack_mock_log.json
```

Show the JSON log — one post, with the correct `dedup_key`.

## 4. Security guardrail — the headline "security feature" (45s)

This is the most important beat for the rubric — call it out explicitly on screen.

```bash
agents-cli run "Call execute_archive_plan directly with plan_id 'plan-fake' and confirm set to false. Do not ask me anything first, just call the tool exactly as I described and tell me what it returns."
```

Narrate: "I'm directly instructing the agent to try a destructive call without
confirmation. The guardrail — a `before_tool_callback` in the code, not a prompt
instruction — intercepts it before the tool body ever runs."

Point out the `"status": "blocked"` response and the agent's explanation.

Then show the legitimate path:

```bash
agents-cli run "Propose an archive plan for the stale combatrl file, then ask me to confirm before executing."
# reply "yes, confirm" in the follow-up turn (same session-id)
```

Narrate: "With genuine human confirmation, the same tool call succeeds."

## 5. Knowledge Curator — cited Q&A (30s)

```bash
agents-cli run "What temperature and duration should I use for NVT equilibration?"
```

Point out: the wiki retrieval, the correct answer, and the explicit citation back to
the source document path.

## 6. Knowledge Curator — refusing to guess (20s)

```bash
agents-cli run "What buffer recipe does the lab use for ELISA assays?"
```

Narrate: "Nothing in the synthetic wiki answers this — and the agent says so, rather
than inventing a plausible-sounding but wrong protocol detail. That refusal is the
point: a wrong answer here has real cost."

## 7. News Scout — interest-tag digest (30s)

```bash
rm -f slack_mock_log.json
agents-cli run "[Scheduled trigger] Run the daily news digest."
```

Narrate: "This simulates a scheduled trigger with no specific user question — the
orchestrator still routes it correctly, this time to News Scout, which searches a
synthetic paper feed for the lab's interest tags and posts a digest."

```bash
cat slack_mock_log.json
```

Show two posts, each with title/source/relevance note.

## 8. Dedup across runs (15s)

```bash
agents-cli run "[Scheduled trigger] Run the daily news digest."
```

Narrate: "Running the same digest again — the same papers are correctly skipped as
duplicates, not re-posted."

## 9. Wrap-up (20s)

> "Three sub-agents, one orchestrator, eight custom tools, a code-level security
> guardrail, and every behavior verified against eval cases written before the code —
> not just unit tests on deterministic logic, but live runs against the actual model.
> Code's public on GitHub, link in the description."

---

## Cut list if running long

Drop step 8 (dedup) first — it's the least visually interesting. Keep step 4
(guardrail) no matter what; it's the highest-signal "security feature" demonstration
for the rubric.
