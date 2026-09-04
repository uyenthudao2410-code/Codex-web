# Orchestration Wave 2

- Run: `51782d652f084183a5e473dd1c493bba`
- Wave: `799d1fd7a7e2442dbdf088f64ee80d87`
- Objective: Replan the same recovery RUN from the newly exposed sole Python MCP failure after the broker cwd fix made the Node/source/sensitive gates pass. Diagnose only why tests/test_workspace_session_isolation.py::WorkspaceSessionIsolationTests::test_legacy_workspace_context_mapping_fails_closed receives an uncaught UNKNOWN_LEGACY_WORKSPACE ToolFailure from Runtime._tool_invocation_context instead of the expected fail-closed tool result boundary. Do not mutate in this prepare wave. Preserve the already-applied broker cwd fix and all unrelated dirty work.
- Objective revision: `2`
- Objective SHA-256: `3ce68f3179874b2b648abe37e7936f9f6b2fdf83e5f42d168c2596922294aa46`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `208c2d60b3323fcc888c4863e37dd2c0562ef7bd59e8fc30e0e2d734344dc2f4`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35396 | 2026-09-02T06:29:00.244Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 changed evidence materially: the broker cwd regression focused boundary passed; the full Node suite passed 601/601; source-root-clean and repository secret/sensitive check passed. npm run test:all then reached Python MCP and exposed exactly one unrelated deterministic failure: test_legacy_workspace_context_mapping_fails_closed, where UNKNOWN_LEGACY_WORKSPACE escapes from Runtime._tool_invocation_context before the expected tool-call fail-closed response boundary. Diagnose this exact boundary before any further mutation; do not rerun the unchanged full suite. |
| 35397 | 2026-09-02T06:29:00.507Z | observation_span_recorded |  |  |  |
| 35398 | 2026-09-02T06:29:02.048Z | observation_span_recorded |  |  |  |
| 35399 | 2026-09-02T06:29:02.252Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35402 | 2026-09-02T06:29:56.230Z | managed_process_admitted |  |  | owner=default |
| 35403 | 2026-09-02T06:29:56.559Z | managed_process_started |  |  | owner=default |
| 35404 | 2026-09-02T06:29:57.084Z | managed_process_terminal |  |  | owner=default |
| 35405 | 2026-09-02T06:30:08.056Z | managed_process_admitted |  |  | owner=default |
| 35406 | 2026-09-02T06:30:08.456Z | managed_process_started |  |  | owner=default |
| 35407 | 2026-09-02T06:30:08.947Z | managed_process_terminal |  |  | owner=default |
| 35409 | 2026-09-02T06:30:37.232Z | managed_process_admitted |  |  | owner=default |
| 35410 | 2026-09-02T06:30:37.585Z | managed_process_started |  |  | owner=default |
| 35411 | 2026-09-02T06:30:38.091Z | managed_process_terminal |  |  | owner=default |
| 35412 | 2026-09-02T06:30:48.457Z | managed_process_admitted |  |  | owner=default |
| 35413 | 2026-09-02T06:30:48.921Z | managed_process_started |  |  | owner=default |
| 35414 | 2026-09-02T06:30:49.586Z | managed_process_terminal |  |  | owner=default |
| 35415 | 2026-09-02T06:30:59.523Z | managed_process_admitted |  |  | owner=default |
| 35416 | 2026-09-02T06:30:59.890Z | managed_process_started |  |  | owner=default |
| 35417 | 2026-09-02T06:31:00.355Z | managed_process_terminal |  |  | owner=default |
| 35418 | 2026-09-02T06:31:09.516Z | managed_process_admitted |  |  | owner=default |
| 35419 | 2026-09-02T06:31:09.966Z | managed_process_started |  |  | owner=default |
| 35420 | 2026-09-02T06:31:10.559Z | managed_process_terminal |  |  | owner=default |
| 38812 | 2026-09-03T20:09:34.580Z | state_transition | PREFLIGHT | ABORTED | reason=G3_RECONCILE_REPLAN_ABANDONED_SUPERSEDED_BY_G2 |
| 38813 | 2026-09-03T20:09:35.065Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `90`
- Chain head: `24c87cd130ebbc52d46743432677a9e6fe857caf4a65e5cf2ac03695dd90e612`
