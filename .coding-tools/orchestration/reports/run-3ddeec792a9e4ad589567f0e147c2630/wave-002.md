# Orchestration Wave 2

- Run: `3ddeec792a9e4ad589567f0e147c2630`
- Wave: `81838aca67424805b5c31c7c7955ea0f`
- Objective: C4 corrective wave: preserve an explicit --user-data-dir for isolated packaged Recovery Host launches instead of overriding it with the production APPDATA profile, while preserving the default version-1.0 production profile when no explicit override is supplied. Add the smallest focused regression oracle. Do not alter scripts/packaged-recovery-smoke.js, unrelated WIP, .coding-tools evidence, Git history, publication, deployment, or the production profile.
- Objective revision: `2`
- Objective SHA-256: `88fda37ca2931ee4f6edffd1f220eb59e432b2f51c6ba1ac1066f486c43128ec`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9b3241ddc963a77d916edc453ea7b7e8e4ae5391`
- Worktree fingerprint: `fdd8e149738afdf61018d6d549f8cfa27ec4acd6f0b714ea56d1e423ae2eeeb6`
- Contract fingerprint: `4aada5917b37cd5c5064b1b1917a78d3ac21fae6f1d94004fcc6dc3222202822`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41336 | 2026-09-06T04:28:59.058Z | wave_replanned |  | PREFLIGHT | reason=Changed strategy after proven C4 failure: Wave 1 established that electron/main.js overrides the smoke's explicit isolated --user-data-dir with production APPDATA, causing the packaged child to encounter the live production recovery-host.lock and exit RECOVERY_HOST_ALREADY_RUNNING. Wave 2 will make the smallest source correction and add a focused regression oracle; it will not retry the unchanged implementation. |
| 41337 | 2026-09-06T04:28:59.273Z | observation_span_recorded |  |  |  |
| 41338 | 2026-09-06T04:29:05.074Z | observation_span_recorded |  |  |  |
| 41339 | 2026-09-06T04:29:05.250Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41340 | 2026-09-06T04:29:20.116Z | managed_process_admitted |  |  | owner=default |
| 41341 | 2026-09-06T04:29:20.430Z | managed_process_started |  |  | owner=default |
| 41342 | 2026-09-06T04:29:20.918Z | managed_process_terminal |  |  | owner=default |
| 41366 | 2026-09-06T04:31:43.640Z | managed_process_admitted |  |  | owner=default |
| 41367 | 2026-09-06T04:31:43.947Z | managed_process_started |  |  | owner=default |
| 41368 | 2026-09-06T04:31:44.558Z | managed_process_terminal |  |  | owner=default |
| 41369 | 2026-09-06T04:31:53.603Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 41370 | 2026-09-06T04:31:53.770Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 41371 | 2026-09-06T04:31:53.973Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `263`
- Chain head: `7149c09e72d121854a41a8b92e9baf22e724d6b02439bd77c368e074ed1bd0e5`
