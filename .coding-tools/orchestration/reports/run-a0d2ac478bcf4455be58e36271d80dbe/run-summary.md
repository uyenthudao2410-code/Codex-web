# Orchestration Run Summary

- Run: `a0d2ac478bcf4455be58e36271d80dbe`
- Task: `6512ce89e798494cabbcc7c8936878ac`
- Objective: Implement token-accounting wave 2 only: make pricing consume canonical non-overlapping token categories without cache/reasoning double count; make durable ledger expose exact 7-day UsageEvent analytics across all runs (hourly UTC, by actor/provider/model, rolling 5 minutes, measured-vs-derived cost provenance) without any LIMIT=8/500 truncation; reject same usage_id with conflicting evidence; keep recent_usage_events(limit=8) as debug-only; exclude controller actor events from provider_economics; expose the 7-day analytics in the existing control orchestration snapshot. Add focused deterministic tests. Preserve accepted UsageEvent v2 semantics and all unrelated dirty source. No ChatWeb ingress/dashboard changes yet. No commit/push/restart.
- Status: **aborted**
- Started: `2026-08-19T08:53:57.058Z`
- Finished: `2026-08-19T08:54:33.775Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a17c1b8d04eb4c94b7b2f44574d4430c` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `8`
- Chain head: `478bdfb0fd0f4c4c25454a3d904a2b38878329dcae4c779144a3dc3b190a2e84`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
