# Orchestration Wave 1

- Run: `7f02ca97c017448098364c1d2f7cd14f`
- Wave: `b8ead2c5b672439a93c15dcb1d6d91a1`
- Objective: Read-only final audit after the accepted canonical Operations Overview patch. Determine whether any visible token/cost field in the same Operations Overview page still consumes the dead legacy measuredUsage aggregation or estimated model-visible bytes without an explicit ESTIMATED label. Focus on secondary model/fleet table, legacy measuredUsage references, modelBreakdown, toolBreakdown, and all calls to renderModelTable/renderFleetTable. If no user-visible inconsistency remains, do not change source. If a residual path exists, identify the smallest cleanup patch and focused oracle. No restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `fd3cd2f12d038d7aece8f2fbe80b19e02c4d4189075037a6f41f1dcf9f8133e7`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21447 | 2026-08-19T10:00:38.787Z | run_started |  | PREFLIGHT |  |
| 21448 | 2026-08-19T10:00:39.788Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21449 | 2026-08-19T10:01:46.715Z | managed_process_admitted |  |  | owner=default |
| 21450 | 2026-08-19T10:01:47.015Z | managed_process_started |  |  | owner=default |
| 21451 | 2026-08-19T10:01:47.466Z | managed_process_terminal |  |  | owner=default |
| 21452 | 2026-08-19T10:01:54.954Z | managed_process_admitted |  |  | owner=default |
| 21453 | 2026-08-19T10:01:55.204Z | managed_process_started |  |  | owner=default |
| 21454 | 2026-08-19T10:01:55.622Z | managed_process_terminal |  |  | owner=default |
| 21455 | 2026-08-19T10:02:05.163Z | managed_process_admitted |  |  | owner=default |
| 21456 | 2026-08-19T10:02:05.430Z | managed_process_started |  |  | owner=default |
| 21457 | 2026-08-19T10:02:06.780Z | managed_process_terminal |  |  | owner=default |
| 21458 | 2026-08-19T10:02:15.346Z | managed_process_admitted |  |  | owner=default |
| 21459 | 2026-08-19T10:02:15.613Z | managed_process_started |  |  | owner=default |
| 21460 | 2026-08-19T10:02:15.996Z | managed_process_terminal |  |  | owner=default |
| 21461 | 2026-08-19T10:02:23.588Z | managed_process_admitted |  |  | owner=default |
| 21462 | 2026-08-19T10:02:23.822Z | managed_process_started |  |  | owner=default |
| 21463 | 2026-08-19T10:02:25.080Z | managed_process_terminal |  |  | owner=default |
| 21464 | 2026-08-19T10:02:33.079Z | managed_process_admitted |  |  | owner=default |
| 21465 | 2026-08-19T10:02:33.346Z | managed_process_started |  |  | owner=default |
| 21466 | 2026-08-19T10:02:34.464Z | managed_process_terminal |  |  | owner=default |
| 21467 | 2026-08-19T10:02:54.236Z | managed_process_admitted |  |  | owner=default |
| 21468 | 2026-08-19T10:02:54.523Z | managed_process_started |  |  | owner=default |
| 21469 | 2026-08-19T10:02:55.030Z | managed_process_terminal |  |  | owner=default |
| 21470 | 2026-08-19T10:03:21.211Z | state_transition | PREFLIGHT | ABORTED | reason=task_stopped |
| 21471 | 2026-08-19T10:03:21.764Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `9eda18cd4c5aa9b80c296937ca77071bda02aa87700e09b7b066fc2901f7868e`
