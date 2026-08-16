# Orchestration Wave 1

- Run: `1739e35082cc4ba9bd29429a8ba10b9c`
- Wave: `bbaaadd6a49640ee9dfeb11d04d4876c`
- Objective: Diagnose and localize the orchestration lifecycle bug evidenced by run 761f3b60b16c4be6a0dc9b1f43881173: the outer durable agent_workflow operation hit WORKFLOW_RUNTIME_EXCEEDED at 600s while its inner proof command continued, was later recorded as passed, a second proof command was admitted after the outer deadline, the canonical EOCL run was later ABORTED, but task-state/UI remained waiting at 'Awaiting acceptance'. Find the smallest coherent fix so workflow deadline terminalizes/cancels remaining proof execution, no next command is launched after deadline/cancel, timeout is never recorded as passed proof solely because exit_code is 0 after forced termination, and task projection reconciles terminal ABORTED/REPLAN states instead of showing Awaiting acceptance. Also identify tests to reproduce this without a 600s sleep. Do not modify files in prepare.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `3c000d27b7d4f82e80753152b331cae18c96cb871d659dd29dc1cf9a82ec9ff6`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8415 | 2026-08-16T13:43:34.910Z | run_started |  | PREFLIGHT |  |
| 8416 | 2026-08-16T13:43:40.697Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8417 | 2026-08-16T13:50:50.593Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8418 | 2026-08-16T13:50:52.716Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8419 | 2026-08-16T13:50:54.001Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8420 | 2026-08-16T13:50:54.910Z | state_transition | READY | ROUTED | reason=route_selected |
| 8421 | 2026-08-16T13:50:56.812Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c044f88457b84a6fbe2fb5c23f326db9 |
| 8422 | 2026-08-16T13:50:57.283Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8423 | 2026-08-16T13:50:59.146Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c044f88457b84a6fbe2fb5c23f326db9 |
| 8424 | 2026-08-16T13:50:59.472Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8425 | 2026-08-16T13:51:00.249Z | proof_cache_miss |  |  | reason=cold; stage_id=check:783e1e3c1245ad4e; input_fingerprint=5fb27a6bdc14ae0b1732aee495e9a7bba71014e172d5a26c8a0b9a0c4b6350cb |
| 8426 | 2026-08-16T13:51:01.330Z | managed_process_admitted |  |  | owner=default |
| 8427 | 2026-08-16T13:51:02.955Z | managed_process_started |  |  | owner=default |
| 8428 | 2026-08-16T13:51:03.522Z | managed_process_terminal |  |  | owner=default |
| 8429 | 2026-08-16T13:51:03.813Z | proof_recorded |  |  | stage_id=check:783e1e3c1245ad4e; status=passed; cache_hit=False; input_fingerprint=5fb27a6bdc14ae0b1732aee495e9a7bba71014e172d5a26c8a0b9a0c4b6350cb |
| 8430 | 2026-08-16T13:51:03.972Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f19cd0191a0ba74f; input_fingerprint=5224f31214159281d926431999c8a83ba13974ce65be3ab5abdf1296c9e8ca10 |
| 8431 | 2026-08-16T13:51:04.294Z | managed_process_admitted |  |  | owner=default |
| 8432 | 2026-08-16T13:51:04.566Z | managed_process_started |  |  | owner=default |
| 8433 | 2026-08-16T13:51:07.799Z | managed_process_terminal |  |  | owner=default |
| 8434 | 2026-08-16T13:51:08.086Z | proof_recorded |  |  | stage_id=check:f19cd0191a0ba74f; status=failed; cache_hit=False; input_fingerprint=5224f31214159281d926431999c8a83ba13974ce65be3ab5abdf1296c9e8ca10 |
| 8435 | 2026-08-16T13:51:08.202Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8436 | 2026-08-16T13:51:08.315Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8437 | 2026-08-16T13:51:08.468Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:783e1e3c1245ad4e | passed | 5fb27a6bdc14ae0b1732aee495e9a7bba71014e172d5a26c8a0b9a0c4b6350cb | False | 2973 | 0 |
| check:f19cd0191a0ba74f | failed | 5224f31214159281d926431999c8a83ba13974ce65be3ab5abdf1296c9e8ca10 | False | 3859 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `adf31dfa175b1bd0d91e77598e18bb28abee79b22b8c51b2124e2fa3efd6ab6c`
