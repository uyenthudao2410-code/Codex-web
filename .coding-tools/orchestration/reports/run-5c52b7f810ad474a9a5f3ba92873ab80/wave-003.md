# Orchestration Wave 3

- Run: `5c52b7f810ad474a9a5f3ba92873ab80`
- Wave: `53089bd8aa994af99a2d055e0cf78398`
- Objective: Fix the confirmed MCP 2026-07-28 stateless cross-tab/default projection leak. Modern stateless requests currently use process-global control_runtime with empty execution_context_id, causing ContextualTaskStateStore and exec_command/task projection to fall back to the global task/run. Implement an application-layer opaque task_context_id carried by tool calls: every modern request must get a nonempty isolated execution scope; supplied task_context_id must deterministically restore the same scope; missing task_context_id must mint a new isolated context rather than inherit global state; strip the common handle before business-tool validation/dispatch as needed; return the handle in modern results so clients can reuse it. Preserve legacy 2025 session behavior, workspace isolation, operator-report latch, accepted unrelated usage_events.py changes, and exactly 8 smart-v3 tools. Do not open P5. Prepare only; no mutation yet.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `f61ba955c5b0c36f72fa8d077a1c894eaca9ee8f54e35a9cffbd5b5d811d0605`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21009 | 2026-08-19T08:50:05.653Z | wave_replanned |  | PREFLIGHT | reason=The explicit stateless task-context patch is now present in three files and fresh verification exposed exactly one failing regression. Changed strategy: inspect the current patched source and isolate that single failure before any further mutation; preserve the other 21 passing tests and do not broaden scope. |
| 21010 | 2026-08-19T08:50:06.918Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21011 | 2026-08-19T08:50:20.938Z | managed_process_admitted |  |  | owner=default |
| 21012 | 2026-08-19T08:50:21.226Z | managed_process_started |  |  | owner=default |
| 21013 | 2026-08-19T08:50:29.197Z | managed_process_terminal |  |  | owner=default |
| 21014 | 2026-08-19T08:50:58.656Z | managed_process_admitted |  |  | owner=default |
| 21015 | 2026-08-19T08:50:59.063Z | managed_process_started |  |  | owner=default |
| 21016 | 2026-08-19T08:51:00.731Z | managed_process_terminal |  |  | owner=default |
| 21017 | 2026-08-19T08:51:14.708Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21018 | 2026-08-19T08:51:25.921Z | managed_process_admitted |  |  | owner=default |
| 21019 | 2026-08-19T08:51:26.238Z | managed_process_started |  |  | owner=default |
| 21020 | 2026-08-19T08:51:26.728Z | managed_process_terminal |  |  | owner=default |
| 21021 | 2026-08-19T08:51:39.548Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21022 | 2026-08-19T08:51:39.689Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21023 | 2026-08-19T08:51:39.863Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21024 | 2026-08-19T08:51:40.160Z | state_transition | READY | ROUTED | reason=route_selected |
| 21025 | 2026-08-19T08:51:40.601Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=01a32b3d327d4549b8856fd59f999553 |
| 21026 | 2026-08-19T08:51:40.786Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21027 | 2026-08-19T08:51:41.167Z | patch_surface_observed |  |  |  |
| 21028 | 2026-08-19T08:51:41.454Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=01a32b3d327d4549b8856fd59f999553 |
| 21029 | 2026-08-19T08:51:41.611Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21030 | 2026-08-19T08:51:41.941Z | proof_cache_miss |  |  | reason=cold; stage_id=check:35688ce7fe1cc1ab; input_fingerprint=9099802f7e952488a059172f62d7fa6ebc85a2dacea6d6aeabb8ed0a768e4f47 |
| 21031 | 2026-08-19T08:51:42.221Z | managed_process_admitted |  |  | owner=default |
| 21032 | 2026-08-19T08:51:42.584Z | managed_process_started |  |  | owner=default |
| 21033 | 2026-08-19T08:51:43.218Z | managed_process_terminal |  |  | owner=default |
| 21034 | 2026-08-19T08:51:43.538Z | proof_recorded |  |  | stage_id=check:35688ce7fe1cc1ab; status=passed; cache_hit=False; input_fingerprint=9099802f7e952488a059172f62d7fa6ebc85a2dacea6d6aeabb8ed0a768e4f47 |
| 21035 | 2026-08-19T08:51:43.721Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9786ed7dff751e1c0855aa6d0e2b2f8449aa4b0f4f84c557509e46ccf7cf43e7 |
| 21036 | 2026-08-19T08:51:44.346Z | managed_process_admitted |  |  | owner=default |
| 21037 | 2026-08-19T08:51:44.621Z | managed_process_started |  |  | owner=default |
| 21038 | 2026-08-19T08:52:03.130Z | managed_process_terminal |  |  | owner=default |
| 21039 | 2026-08-19T08:52:03.431Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9786ed7dff751e1c0855aa6d0e2b2f8449aa4b0f4f84c557509e46ccf7cf43e7 |
| 21040 | 2026-08-19T08:52:03.907Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21041 | 2026-08-19T08:52:19.466Z | quality_outcome_recorded |  |  |  |
| 21042 | 2026-08-19T08:52:19.750Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21043 | 2026-08-19T08:52:20.074Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:35688ce7fe1cc1ab | passed | 9099802f7e952488a059172f62d7fa6ebc85a2dacea6d6aeabb8ed0a768e4f47 | False | 1303 | 0 |
| verify:tests | passed | 9786ed7dff751e1c0855aa6d0e2b2f8449aa4b0f4f84c557509e46ccf7cf43e7 | False | 19250 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 238634314e1c4c96b7c59c1668ed9ae6 | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | 515c324d22c4d571313cba44ba2a96f92c4dfda14477d15b1f3364e2cc22bab8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `25a938ad238fc51fc4cdafb1ad759cf4fd458a4ffe41cde30fb82211eed90cc6`
