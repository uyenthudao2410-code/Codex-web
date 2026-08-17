# Orchestration Wave 1

- Run: `f6c9de68597b442fa51c570ec712dba9`
- Wave: `7cf8805da9b34e25a4a4db38e429fa63`
- Objective: READ ONLY. Diagnose the Coding MCP connection/runtime routing architecture responsible for one ChatGPT plugin session landing workspace_context on E:\DEV\Tools-Codex-web while exec_command/agent_workflow land E:\Github\Tools-Codex-web. Do not mutate. Localize HTTP session creation, runtime selection, workspace switching, hub client identity, Electron supervisor registration/health/restart, and any stale endpoint/fallback behavior. Recommend the smallest fail-closed session-affinity fix with exact files/symbols and focused tests.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `66e2408b22c3a87b460f6faaae950b9ec2972f1354d6ccd7c9562ef2f3f1c4db`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11060 | 2026-08-17T03:26:33.956Z | run_started |  | PREFLIGHT |  |
| 11061 | 2026-08-17T03:26:36.979Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11062 | 2026-08-17T03:26:53.129Z | managed_process_admitted |  |  | owner=chatweb |
| 11063 | 2026-08-17T03:26:53.380Z | managed_process_started |  |  | owner=chatweb |
| 11064 | 2026-08-17T03:26:54.035Z | managed_process_terminal |  |  | owner=chatweb |
| 11065 | 2026-08-17T03:27:23.146Z | managed_process_admitted |  |  | owner=chatweb |
| 11066 | 2026-08-17T03:27:23.497Z | managed_process_started |  |  | owner=chatweb |
| 11067 | 2026-08-17T03:27:24.179Z | managed_process_terminal |  |  | owner=chatweb |
| 11068 | 2026-08-17T03:29:46.944Z | managed_process_admitted |  |  | owner=chatweb |
| 11069 | 2026-08-17T03:29:47.205Z | managed_process_started |  |  | owner=chatweb |
| 11070 | 2026-08-17T03:29:47.843Z | managed_process_terminal |  |  | owner=chatweb |
| 11071 | 2026-08-17T03:30:11.028Z | managed_process_admitted |  |  | owner=chatweb |
| 11072 | 2026-08-17T03:30:11.330Z | managed_process_started |  |  | owner=chatweb |
| 11073 | 2026-08-17T03:30:16.423Z | managed_process_terminal |  |  | owner=chatweb |
| 11074 | 2026-08-17T03:30:30.779Z | managed_process_admitted |  |  | owner=chatweb |
| 11075 | 2026-08-17T03:30:31.071Z | managed_process_started |  |  | owner=chatweb |
| 11076 | 2026-08-17T03:30:31.714Z | managed_process_terminal |  |  | owner=chatweb |
| 11077 | 2026-08-17T03:35:30.110Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 11078 | 2026-08-17T03:35:30.286Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 11079 | 2026-08-17T03:35:30.475Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `58`
- Chain head: `fdfe464941c3fc0c9026005fd8647c435a1d4aac3b3b933cab9d7887ae7d9332`
