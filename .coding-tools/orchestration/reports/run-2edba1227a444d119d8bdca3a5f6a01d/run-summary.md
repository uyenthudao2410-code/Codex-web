# Orchestration Run Summary

- Run: `2edba1227a444d119d8bdca3a5f6a01d`
- Task: `33d68bf3cf1748399d15b1f02bd8f39f`
- Objective: Continue the same read-only diagnosis of accepted restart ticket restart-Tk0y31JsQ9krhgaQ not being consumed before TTL. Materialize only the exact RuntimeOrchestrator.supervise control flow after serviceSupervisorRestartRequest plus state transitions that can suppress later ticket retries. Determine whether a deferred RUNTIME_BUSY result can leave this.busy/this.recovering or another gate preventing subsequent .processing journal consumption. No mutation, no restart, no cleanup.
- Status: **aborted**
- Started: `2026-08-27T19:34:09.519Z`
- Finished: `2026-08-27T19:40:00.882Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a3f2e57451e346bbab32b28b4ce20c46` | 1 | `run_initial_objective` | `mcp_only` | `b64c43c7e092301dd9abdfad32d4dc1910192485` | aborted |

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
- Events checked: `9`
- Chain head: `aac8c4896f195671641c62cb2dba2f45371d9a4ff4133d6edbf387a7a372c094`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
