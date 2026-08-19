# Orchestration Wave 4

- Run: `f65f757cb913400fac3c991be41dcd2c`
- Wave: `a7c66d6f2f934f91ae4e71dc131229ae`
- Objective: Localize the smallest production/test seams to finish same-root multi-tab task/run projection isolation and add a durable completion-report acknowledgement latch. Requirements: independent ChatWeb execution_context_id values on the same workspace/root must resolve to isolated TaskStateStore/projection state; legacy/stateless clients remain compatible; a pending completion_report with operator_visible_required=true must not be silently superseded by start/clear/resume or a new material agent_workflow until explicitly acknowledged; use existing task_control/public 8-tool surface, no new top-level tool and no DB migration unless unavoidable. Preserve current P4 compatibility recovery and unrelated renderer/HR changes.
- Mode: `mcp_only`
- Base HEAD: `359a5f231e1950e8d97303e0d2b798984c145fe6`
- Worktree fingerprint: `b2e458bd64be9a29a8cf8cf457e75b19121ede1000c1c69ac7178ab4c3bc65a0`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20528 | 2026-08-19T07:12:45.067Z | wave_replanned |  | PREFLIGHT | reason=Proof 614a225b4cb0496dacf7a2249e341107 now has exactly two failures, both asserting legacy owner_client_id='chatweb' while the new compatibility session fencing emits chatweb:<execution_context>. Inspect the oracle and identity construction before changing expectations; no production change is assumed. |
| 20529 | 2026-08-19T07:12:45.778Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20530 | 2026-08-19T07:12:46.292Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20531 | 2026-08-19T07:12:46.578Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20532 | 2026-08-19T07:12:46.940Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20533 | 2026-08-19T07:12:54.887Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20534 | 2026-08-19T07:12:55.103Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20535 | 2026-08-19T07:12:55.426Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20536 | 2026-08-19T07:13:03.177Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20537 | 2026-08-19T07:13:03.370Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20538 | 2026-08-19T07:13:03.716Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20539 | 2026-08-19T07:13:10.026Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20540 | 2026-08-19T07:13:10.254Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20541 | 2026-08-19T07:13:10.592Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20542 | 2026-08-19T07:13:19.017Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20543 | 2026-08-19T07:13:19.184Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20544 | 2026-08-19T07:13:19.342Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20545 | 2026-08-19T07:13:19.463Z | state_transition | READY | ROUTED | reason=route_selected |
| 20546 | 2026-08-19T07:13:19.855Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=34eeff7a8d224925bbd443c4cf49f0fb |
| 20547 | 2026-08-19T07:13:19.986Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20548 | 2026-08-19T07:13:20.345Z | patch_surface_observed |  |  |  |
| 20549 | 2026-08-19T07:13:20.846Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=34eeff7a8d224925bbd443c4cf49f0fb |
| 20550 | 2026-08-19T07:13:20.979Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20551 | 2026-08-19T07:13:21.368Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=05a50b73f51550e907bc2b5a1c72e94453e1fc1cfc273c6a5884ac485b399858 |
| 20552 | 2026-08-19T07:13:21.687Z | managed_process_admitted |  |  | owner=default |
| 20553 | 2026-08-19T07:13:21.954Z | managed_process_started |  |  | owner=default |
| 20554 | 2026-08-19T07:13:24.821Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20555 | 2026-08-19T07:13:25.069Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20556 | 2026-08-19T07:13:25.441Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20557 | 2026-08-19T07:13:31.921Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20558 | 2026-08-19T07:13:32.145Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20559 | 2026-08-19T07:13:32.508Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20560 | 2026-08-19T07:13:40.301Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20561 | 2026-08-19T07:13:40.537Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20562 | 2026-08-19T07:13:40.959Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20563 | 2026-08-19T07:13:54.041Z | managed_process_terminal |  |  | owner=default |
| 20564 | 2026-08-19T07:13:54.349Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=05a50b73f51550e907bc2b5a1c72e94453e1fc1cfc273c6a5884ac485b399858 |
| 20565 | 2026-08-19T07:13:54.514Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 20566 | 2026-08-19T07:13:54.697Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 20567 | 2026-08-19T07:13:54.860Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 05a50b73f51550e907bc2b5a1c72e94453e1fc1cfc273c6a5884ac485b399858 | False | 32687 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `176`
- Chain head: `94710588eaf69582decd1be878dfb6f1b4d44d323b09064325c8ab3bd640d517`
