# Orchestration Wave 1

- Run: `3b978ca3ccb840c1aee84bc122b2a4a6`
- Wave: `c5aed396c3a2494fa513ec46efb61f4f`
- Objective: S2 final proof-only preflight. Locate the exact focused existing tests and source symbols needed to prove: provider_result artifact_ref wiring, orchestration_proof artifact_ref, handoff_capsule artifact_ref, build_artifact artifact_ref, bounded read_project_artifact offset/length/default/max behavior, and native image retrieval MIME plus SHA-256 integrity. The command_output lineage wave is already accepted and should be reused, not rerun. No writes, no docs, no S3. Return exact test names/commands and relevant symbols with minimal context.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `ac0b969589034b068376451202c12961a81726dbdc2e12be3a52d37d8731eba8`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24539 | 2026-08-20T23:53:04.471Z | run_started |  | PREFLIGHT |  |
| 24540 | 2026-08-20T23:53:05.500Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 24541 | 2026-08-20T23:53:23.686Z | managed_process_admitted |  |  | owner=default |
| 24542 | 2026-08-20T23:53:24.002Z | managed_process_started |  |  | owner=default |
| 24543 | 2026-08-20T23:53:24.435Z | managed_process_terminal |  |  | owner=default |
| 24544 | 2026-08-20T23:53:29.962Z | managed_process_admitted |  |  | owner=default |
| 24545 | 2026-08-20T23:53:30.275Z | managed_process_started |  |  | owner=default |
| 24546 | 2026-08-20T23:53:30.712Z | managed_process_terminal |  |  | owner=default |
| 24547 | 2026-08-20T23:53:38.918Z | managed_process_admitted |  |  | owner=default |
| 24548 | 2026-08-20T23:53:39.240Z | managed_process_started |  |  | owner=default |
| 24549 | 2026-08-20T23:53:39.657Z | managed_process_terminal |  |  | owner=default |
| 24550 | 2026-08-20T23:53:45.885Z | managed_process_admitted |  |  | owner=default |
| 24551 | 2026-08-20T23:53:46.209Z | managed_process_started |  |  | owner=default |
| 24552 | 2026-08-20T23:53:46.585Z | managed_process_terminal |  |  | owner=default |
| 24553 | 2026-08-20T23:53:51.652Z | managed_process_admitted |  |  | owner=default |
| 24554 | 2026-08-20T23:53:51.960Z | managed_process_started |  |  | owner=default |
| 24555 | 2026-08-20T23:53:52.452Z | managed_process_terminal |  |  | owner=default |
| 24556 | 2026-08-20T23:54:05.069Z | managed_process_admitted |  |  | owner=default |
| 24557 | 2026-08-20T23:54:05.385Z | managed_process_started |  |  | owner=default |
| 24558 | 2026-08-20T23:54:05.929Z | managed_process_terminal |  |  | owner=default |
| 24559 | 2026-08-20T23:54:07.101Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 24560 | 2026-08-20T23:54:11.469Z | managed_process_admitted |  |  | owner=default |
| 24561 | 2026-08-20T23:54:11.810Z | managed_process_started |  |  | owner=default |
| 24562 | 2026-08-20T23:54:12.311Z | managed_process_terminal |  |  | owner=default |
| 24563 | 2026-08-20T23:54:18.817Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 24564 | 2026-08-20T23:54:20.451Z | managed_process_admitted |  |  | owner=default |
| 24565 | 2026-08-20T23:54:20.817Z | managed_process_started |  |  | owner=default |
| 24566 | 2026-08-20T23:54:21.185Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24567 | 2026-08-20T23:54:27.051Z | managed_process_admitted |  |  | owner=default |
| 24568 | 2026-08-20T23:54:27.376Z | managed_process_started |  |  | owner=default |
| 24569 | 2026-08-20T23:54:27.800Z | managed_process_terminal |  |  | owner=default |
| 24570 | 2026-08-20T23:54:33.850Z | managed_process_admitted |  |  | owner=default |
| 24571 | 2026-08-20T23:54:34.111Z | managed_process_started |  |  | owner=default |
| 24572 | 2026-08-20T23:54:34.590Z | managed_process_terminal |  |  | owner=default |
| 24573 | 2026-08-20T23:54:41.217Z | managed_process_admitted |  |  | owner=default |
| 24574 | 2026-08-20T23:54:41.510Z | managed_process_started |  |  | owner=default |
| 24575 | 2026-08-20T23:54:42.016Z | managed_process_terminal |  |  | owner=default |
| 24576 | 2026-08-20T23:54:46.319Z | managed_process_admitted |  |  | owner=default |
| 24577 | 2026-08-20T23:54:46.583Z | managed_process_started |  |  | owner=default |
| 24578 | 2026-08-20T23:54:46.950Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24579 | 2026-08-20T23:55:01.783Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24580 | 2026-08-20T23:55:02.033Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24581 | 2026-08-20T23:55:02.198Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 24582 | 2026-08-20T23:55:02.467Z | state_transition | READY | ROUTED | reason=route_selected |
| 24583 | 2026-08-20T23:55:02.952Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=55995c05db8749a7b15e156107786f5a |
| 24584 | 2026-08-20T23:55:03.135Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24585 | 2026-08-20T23:55:03.566Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=55995c05db8749a7b15e156107786f5a |
| 24586 | 2026-08-20T23:55:03.732Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24587 | 2026-08-20T23:55:04.033Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f9725f9f56dd6d35; input_fingerprint=08a623b405154072efb8f625d785e1f187b96e3f7fb37c5692569c17f15b0fd3 |
| 24588 | 2026-08-20T23:55:04.367Z | managed_process_admitted |  |  | owner=default |
| 24589 | 2026-08-20T23:55:04.707Z | managed_process_started |  |  | owner=default |
| 24590 | 2026-08-20T23:55:05.083Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24591 | 2026-08-20T23:55:05.516Z | proof_recorded |  |  | stage_id=check:f9725f9f56dd6d35; status=failed; cache_hit=False; input_fingerprint=08a623b405154072efb8f625d785e1f187b96e3f7fb37c5692569c17f15b0fd3 |
| 24592 | 2026-08-20T23:55:05.694Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 24593 | 2026-08-20T23:55:05.869Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 24594 | 2026-08-20T23:55:06.069Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f9725f9f56dd6d35 | failed | 08a623b405154072efb8f625d785e1f187b96e3f7fb37c5692569c17f15b0fd3 | False | 899 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `99`
- Chain head: `5390ad5c46e8f2b721c12ae13fcbd904760924da26af1508dba28683191b8c51`
