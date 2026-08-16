# Orchestration Wave 2

- Run: `1739e35082cc4ba9bd29429a8ba10b9c`
- Wave: `10d8d913be294df49454d7a69840c3af`
- Objective: Diagnose and localize the orchestration lifecycle bug evidenced by run 761f3b60b16c4be6a0dc9b1f43881173: the outer durable agent_workflow operation hit WORKFLOW_RUNTIME_EXCEEDED at 600s while its inner proof command continued, was later recorded as passed, a second proof command was admitted after the outer deadline, the canonical EOCL run was later ABORTED, but task-state/UI remained waiting at 'Awaiting acceptance'. Find the smallest coherent fix so workflow deadline terminalizes/cancels remaining proof execution, no next command is launched after deadline/cancel, timeout is never recorded as passed proof solely because exit_code is 0 after forced termination, and task projection reconciles terminal ABORTED/REPLAN states instead of showing Awaiting acceptance. Also identify tests to reproduce this without a 600s sleep. Do not modify files in prepare.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `9e7ef9a96166e0bd1ab9c86cadea8457ed3bb38d757a1347bd7c9ba0345fd1c5`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8438 | 2026-08-16T13:51:38.879Z | wave_replanned |  | PREFLIGHT | reason=Previous proof command was launched from repository root and failed test collection with ModuleNotFoundError: coding_tools_mcp. Source compiled successfully. Change only the proof working directory to resources/coding-tools-mcp; do not retry the same invalid environment. |
| 8439 | 2026-08-16T13:51:39.015Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8440 | 2026-08-16T13:51:39.126Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8441 | 2026-08-16T13:51:39.267Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8442 | 2026-08-16T13:51:39.534Z | state_transition | READY | ROUTED | reason=route_selected |
| 8443 | 2026-08-16T13:51:40.452Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=006ee196d2564ce5967492ddfbbd3b43 |
| 8444 | 2026-08-16T13:51:40.696Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8445 | 2026-08-16T13:51:41.729Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=006ee196d2564ce5967492ddfbbd3b43 |
| 8446 | 2026-08-16T13:51:42.005Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8447 | 2026-08-16T13:51:42.654Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b69f7a0f72cac8c9; input_fingerprint=59ee19754d2b9c8a0e82ed3ebc3eb11c7f6e9a0012dd9d44ebd9cdd3881f753f |
| 8448 | 2026-08-16T13:51:43.207Z | managed_process_admitted |  |  | owner=default |
| 8449 | 2026-08-16T13:51:43.529Z | managed_process_started |  |  | owner=default |
| 8450 | 2026-08-16T13:51:44.564Z | managed_process_terminal |  |  | owner=default |
| 8451 | 2026-08-16T13:51:45.053Z | proof_recorded |  |  | stage_id=check:b69f7a0f72cac8c9; status=passed; cache_hit=False; input_fingerprint=59ee19754d2b9c8a0e82ed3ebc3eb11c7f6e9a0012dd9d44ebd9cdd3881f753f |
| 8452 | 2026-08-16T13:51:45.405Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2aa53151018e67a7; input_fingerprint=fb189ddef3bdb8f94f478c53e552aa2aece6ced91e9d660e034999f153d7ab72 |
| 8453 | 2026-08-16T13:51:46.030Z | managed_process_admitted |  |  | owner=default |
| 8454 | 2026-08-16T13:51:46.471Z | managed_process_started |  |  | owner=default |
| 8455 | 2026-08-16T13:51:51.198Z | managed_process_terminal |  |  | owner=default |
| 8456 | 2026-08-16T13:51:51.455Z | proof_recorded |  |  | stage_id=check:2aa53151018e67a7; status=passed; cache_hit=False; input_fingerprint=fb189ddef3bdb8f94f478c53e552aa2aece6ced91e9d660e034999f153d7ab72 |
| 8457 | 2026-08-16T13:51:51.587Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b07652254b3b7af2; input_fingerprint=fc78f721dd4170b3e8fe2f3ccf3eba9ccfbee23bd1d8e89d2207f28546c8bac1 |
| 8458 | 2026-08-16T13:51:52.102Z | managed_process_admitted |  |  | owner=default |
| 8459 | 2026-08-16T13:51:52.496Z | managed_process_started |  |  | owner=default |
| 8460 | 2026-08-16T13:51:55.174Z | managed_process_terminal |  |  | owner=default |
| 8461 | 2026-08-16T13:51:55.417Z | proof_recorded |  |  | stage_id=check:b07652254b3b7af2; status=passed; cache_hit=False; input_fingerprint=fc78f721dd4170b3e8fe2f3ccf3eba9ccfbee23bd1d8e89d2207f28546c8bac1 |
| 8462 | 2026-08-16T13:51:55.561Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8463 | 2026-08-16T13:52:12.436Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8464 | 2026-08-16T13:52:13.165Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b69f7a0f72cac8c9 | passed | 59ee19754d2b9c8a0e82ed3ebc3eb11c7f6e9a0012dd9d44ebd9cdd3881f753f | False | 1863 | 0 |
| check:2aa53151018e67a7 | passed | fb189ddef3bdb8f94f478c53e552aa2aece6ced91e9d660e034999f153d7ab72 | False | 5583 | 0 |
| check:b07652254b3b7af2 | passed | fc78f721dd4170b3e8fe2f3ccf3eba9ccfbee23bd1d8e89d2207f28546c8bac1 | False | 3481 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6187947743604496b52ecac35f65ff49 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 2b834cff8cbae1095999201a9122f73e708ac4e27d8d500f5824fc5bdb5e491e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `adf31dfa175b1bd0d91e77598e18bb28abee79b22b8c51b2124e2fa3efd6ab6c`
