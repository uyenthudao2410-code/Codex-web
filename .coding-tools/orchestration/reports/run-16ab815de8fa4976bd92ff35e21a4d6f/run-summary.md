# Orchestration Run Summary

- Run: `16ab815de8fa4976bd92ff35e21a4d6f`
- Task: `36fdd59b6fb146648cb91d6a600a3020`
- Objective: Implement and close P1.3 Controller Usage Coverage only. Add a causal explicit experimental-enrollment denominator to current_ledger_baseline controller coverage; count controller started_at/token/cost/source only for enrolled experimental runs, keep missing telemetry unknown, and fail closed for promotion economics when enrolled controller monetary-cost coverage is incomplete. Preserve all-history controller counts only if clearly labeled separately; do not let organic host trace/turn identity enter the experimental denominator. Add focused regression tests. Do not implement P1.4, change routing/public schema/DB, or restart runtime.
- Status: **accepted**
- Started: `2026-08-17T16:24:10.023Z`
- Finished: `2026-08-17T16:28:51.800Z`

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
| 1 | `72524477cded4457858d1ae2e8426e12` | `mcp_only` | `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e448ffb3569f40e697ebdd784b9a2600 | 72524477cded4457858d1ae2e8426e12 | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 84ab8491ec4d290e08cab7af7f24444456121162ba477c060fe30282e3b9c5c6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 14495 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `ff2300b2f71a373369816b0bf92f9e34151f4d003f977faa2f7627f87260344c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
