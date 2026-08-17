# Orchestration Run Summary

- Run: `16c46b4098d14cfba2207226a3ad650f`
- Task: `f2e8fffaa50841adbea4a6cb4640aea5`
- Objective: P2 final readiness reporting closure before P3: add aggregate causal-classification coverage and oracle-observation coverage to the existing rework diagnosis report, using only already observed ledger evidence. Preserve CHECK_FAILED and other unmapped structured failures as unclassified; preserve unknown oracle as unknown; do not change remediation behavior or public schema.
- Status: **accepted**
- Started: `2026-08-17T19:24:43.913Z`
- Finished: `2026-08-17T19:28:14.942Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `50dc3fd12732494d9597e08b8ee5dd74` | `mcp_only` | `775d92716f90ada3cfa909d8f0069c46d204ab51` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 5f21ad9ac88842c7a3e7aa976d9fd8a3 | 50dc3fd12732494d9597e08b8ee5dd74 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | 2345035d0849a5379a5c28630492e11d8e30836ad4c7d852694fe328b666260a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15605 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `388b5aea128dc1d8281337a6e9e896e1123d17909878dbe58cbe1c6cf6d4c0a9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
