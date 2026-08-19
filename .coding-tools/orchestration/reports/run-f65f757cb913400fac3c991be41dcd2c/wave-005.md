# Orchestration Wave 5

- Run: `f65f757cb913400fac3c991be41dcd2c`
- Wave: `8452517718cd4affaac00813ff52104a`
- Objective: Localize the smallest production/test seams to finish same-root multi-tab task/run projection isolation and add a durable completion-report acknowledgement latch. Requirements: independent ChatWeb execution_context_id values on the same workspace/root must resolve to isolated TaskStateStore/projection state; legacy/stateless clients remain compatible; a pending completion_report with operator_visible_required=true must not be silently superseded by start/clear/resume or a new material agent_workflow until explicitly acknowledged; use existing task_control/public 8-tool surface, no new top-level tool and no DB migration unless unavoidable. Preserve current P4 compatibility recovery and unrelated renderer/HR changes.
- Mode: `mcp_only`
- Base HEAD: `359a5f231e1950e8d97303e0d2b798984c145fe6`
- Worktree fingerprint: `c58437b05068bdee6e6b404295fae6b7dfed6fc2099c2812fec8ede7e3e8d24d`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20568 | 2026-08-19T07:14:42.034Z | wave_replanned |  | PREFLIGHT | reason=The sole remaining error is a test-harness protocol mismatch: after compatibility sessions became execution-scoped, the fault test discarded the server-issued Mcp-Session-Id and therefore created a new ChatWeb context on every tools/call. Reusing the issued session is the correct protocol behavior and preserves the intended independent cursor/controller fencing oracle. |
| 20569 | 2026-08-19T07:14:42.187Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20570 | 2026-08-19T07:14:42.407Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20571 | 2026-08-19T07:14:42.566Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20572 | 2026-08-19T07:14:42.881Z | state_transition | READY | ROUTED | reason=route_selected |
| 20573 | 2026-08-19T07:14:43.287Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b0ec59770ff74b0bbfef457ce3a75870 |
| 20574 | 2026-08-19T07:14:43.461Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20575 | 2026-08-19T07:14:43.878Z | patch_surface_observed |  |  |  |
| 20576 | 2026-08-19T07:14:44.188Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b0ec59770ff74b0bbfef457ce3a75870 |
| 20577 | 2026-08-19T07:14:44.336Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20578 | 2026-08-19T07:14:44.671Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=542b395566bba2b582c1e8f66755304885dc8821013200e65224387bc81782b2 |
| 20579 | 2026-08-19T07:14:45.000Z | managed_process_admitted |  |  | owner=default |
| 20580 | 2026-08-19T07:14:45.286Z | managed_process_started |  |  | owner=default |
| 20581 | 2026-08-19T07:14:45.406Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20582 | 2026-08-19T07:14:45.822Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20583 | 2026-08-19T07:14:46.251Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20584 | 2026-08-19T07:14:54.730Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20585 | 2026-08-19T07:14:54.982Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20586 | 2026-08-19T07:14:55.349Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20587 | 2026-08-19T07:15:06.103Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20588 | 2026-08-19T07:15:06.320Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20589 | 2026-08-19T07:15:06.726Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20590 | 2026-08-19T07:15:13.175Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20591 | 2026-08-19T07:15:13.377Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20592 | 2026-08-19T07:15:13.759Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20593 | 2026-08-19T07:15:20.000Z | managed_process_admitted |  |  | owner=hr-cost-code-compact |
| 20594 | 2026-08-19T07:15:20.279Z | managed_process_started |  |  | owner=hr-cost-code-compact |
| 20595 | 2026-08-19T07:15:20.700Z | managed_process_terminal |  |  | owner=hr-cost-code-compact |
| 20596 | 2026-08-19T07:15:21.956Z | managed_process_terminal |  |  | owner=default |
| 20597 | 2026-08-19T07:15:22.272Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=542b395566bba2b582c1e8f66755304885dc8821013200e65224387bc81782b2 |
| 20598 | 2026-08-19T07:15:22.428Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 20599 | 2026-08-19T07:15:22.575Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 20600 | 2026-08-19T07:15:22.721Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 542b395566bba2b582c1e8f66755304885dc8821013200e65224387bc81782b2 | False | 37296 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `176`
- Chain head: `94710588eaf69582decd1be878dfb6f1b4d44d323b09064325c8ab3bd640d517`
