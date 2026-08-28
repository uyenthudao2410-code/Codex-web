# Orchestration Run Summary

- Run: `4ef908da0c9140ffbe95093b52c0e357`
- Task: `bc9d8f603fe0477cb0297ea3d5fd6bff`
- Objective: Continue the same read-only diagnosis. Prove whether Recovery Host and Coding MCP use the same supervisor restart journal path by tracing RuntimePaths.supervisorRequestFile and NativeService launch env into Python coordination. Also materialize RuntimeOrchestrator.supervise around the serviceSupervisorRestartRequest call and any existing source/test evidence for ticket path identity. No mutation and no restart.
- Status: **aborted**
- Started: `2026-08-27T19:33:04.981Z`
- Finished: `2026-08-27T19:40:40.182Z`

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
| 1 | `ed907998ee1f49c8a10caad68c81cc7f` | 1 | `run_initial_objective` | `mcp_only` | `b64c43c7e092301dd9abdfad32d4dc1910192485` | aborted |

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
- Events checked: `6`
- Chain head: `2c44a6f1cd0676deb7ca7ba6ed34cff4fb0fef93b9bb9fcf9e391d3ec3a65054`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
