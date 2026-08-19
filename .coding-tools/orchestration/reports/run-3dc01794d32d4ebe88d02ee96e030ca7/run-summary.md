# Orchestration Run Summary

- Run: `3dc01794d32d4ebe88d02ee96e030ca7`
- Task: `cdf67e2297dc4f65bfedb04053d7b96b`
- Objective: Replacement wave after aborted no-mutation attempt. Implement only pricing + durable ledger token accounting: canonical non-overlapping pricing, 7-day UsageEvent analytics across all runs with exact hourly/by-model/rolling-5m aggregates, strict duplicate evidence, recent_usage_events(limit=8) retained only as debug projection, controller events excluded from provider_economics. Source already has accepted UsageEvent v2 canonicalization. Preserve unrelated changes; no commit/push/restart.
- Status: **aborted**
- Started: `2026-08-19T08:41:27.755Z`
- Finished: `2026-08-19T08:42:22.618Z`

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
| 1 | `6b4c5b28dcd44f4fbce2ee80b7c0dce9` | `auto` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | aborted |

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
- Events checked: `5`
- Chain head: `cb84e7317e27f5c9d0d65548dd355734aab6b464788d087ce26acbb52f60d1d6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
