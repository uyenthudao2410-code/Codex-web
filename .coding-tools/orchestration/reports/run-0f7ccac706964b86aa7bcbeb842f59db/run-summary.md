# Orchestration Run Summary

- Run: `0f7ccac706964b86aa7bcbeb842f59db`
- Task: `61e19db66aa94ad8a1423f9fffbace27`
- Objective: Create three identical isolated benchmark fixtures under tmp/execution-hub-benchmark/{mini,luna,sol} for paired routing evaluation. Each fixture contains the same intentionally broken normalize_score implementation and the same deterministic 3-case oracle. This is benchmark setup only; do not touch production source.
- Status: **accepted**
- Started: `2026-08-14T06:05:32.061Z`
- Finished: `2026-08-14T06:05:49.240Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a9287b52cb2b4b22ba81683128413918` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3c88d72aa62846e3add04c713ec354f6 | a9287b52cb2b4b22ba81683128413918 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1232 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `4ba842a3d952c8404fc6d313d4670720042dd9774603143ddebbe0baa53c51e6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
