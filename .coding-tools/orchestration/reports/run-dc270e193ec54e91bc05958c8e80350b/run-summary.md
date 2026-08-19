# Orchestration Run Summary

- Run: `dc270e193ec54e91bc05958c8e80350b`
- Task: `aa640bc907b9498f81c63f337f142f38`
- Objective: Fix Codex-web realtime performance card with exact rolling 5-minute provider-measured TPM and exact rolling 5-minute command latency, explicit freshness/no-data states, no stale hourly/daily/all-history fallbacks, no backend/public-tool changes, and focused renderer tests only. Preserve unrelated work. No restart, commit, push, or deploy.
- Status: **active**
- Started: `2026-08-19T06:24:47.550Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `03fb3d68da574d838a9b7e86d51fc589` | `mcp_only` | `359a5f231e1950e8d97303e0d2b798984c145fe6` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 20385 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 20394 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 20398 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `7bb72582b4d1641514c1889e5f705c74c30920a5dc299dba1e19352d6b079a8d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
