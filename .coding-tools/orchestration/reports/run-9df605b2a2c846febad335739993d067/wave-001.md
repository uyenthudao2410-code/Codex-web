# Orchestration Wave 1

- Run: `9df605b2a2c846febad335739993d067`
- Wave: `b5b55a6d709f4cfea81705a6165a55f2`
- Objective: Fix the live automatic code-activation state-machine loop on E:\DEV\Tools-Codex-web. Current Recovery Host repeatedly logs BASE_HEAD_CHANGED every ~3 seconds after an activation intent captured an older Git HEAD; it never terminalizes/replans, so newer accepted Recovery Host/UI code cannot activate. Preserve fail-closed revision/device/workspace checks and already accepted legacy revision bridge. Required behavior: when the accepted activation candidate/base HEAD becomes stale before mutation, terminalize or supersede that stale intent deterministically and allow the scheduler to consider the current accepted candidate; never activate a revision proven against a different base. Add a focused regression proving no repeated active loop and that the newer candidate can progress. Do not touch unrelated WIP.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `e4cda10a6bcba9745196dd09c99bf7fb0cc72f7fc578b078abc037d2846b7f48`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11642 | 2026-08-17T05:51:48.564Z | run_started |  | PREFLIGHT |  |
| 11643 | 2026-08-17T05:51:49.379Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11644 | 2026-08-17T05:52:53.576Z | managed_process_admitted |  |  | owner=chatweb |
| 11645 | 2026-08-17T05:52:53.920Z | managed_process_started |  |  | owner=chatweb |
| 11646 | 2026-08-17T05:52:54.667Z | managed_process_terminal |  |  | owner=chatweb |
| 11647 | 2026-08-17T05:53:32.959Z | managed_process_admitted |  |  | owner=chatweb |
| 11648 | 2026-08-17T05:53:33.309Z | managed_process_started |  |  | owner=chatweb |
| 11649 | 2026-08-17T05:53:33.878Z | managed_process_terminal |  |  | owner=chatweb |
| 11650 | 2026-08-17T05:54:46.923Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11651 | 2026-08-17T05:54:47.157Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11652 | 2026-08-17T05:54:47.339Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11653 | 2026-08-17T05:54:47.707Z | state_transition | READY | ROUTED | reason=route_selected |
| 11654 | 2026-08-17T05:54:48.228Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=24469d3433ba4f0f823660979d8007d8 |
| 11655 | 2026-08-17T05:54:48.416Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11656 | 2026-08-17T05:54:49.073Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=24469d3433ba4f0f823660979d8007d8 |
| 11657 | 2026-08-17T05:54:49.257Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11658 | 2026-08-17T05:54:49.679Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7461bc5dce821b50; input_fingerprint=b09d4cbc57ab29dda1ff4e218a90b5fc9fc3bde78855bc86288a8cb5c901090d |
| 11659 | 2026-08-17T05:54:50.055Z | managed_process_admitted |  |  | owner=default |
| 11660 | 2026-08-17T05:54:50.623Z | managed_process_started |  |  | owner=default |
| 11661 | 2026-08-17T05:54:51.090Z | managed_process_terminal |  |  | owner=default |
| 11662 | 2026-08-17T05:54:51.422Z | proof_recorded |  |  | stage_id=check:7461bc5dce821b50; status=passed; cache_hit=False; input_fingerprint=b09d4cbc57ab29dda1ff4e218a90b5fc9fc3bde78855bc86288a8cb5c901090d |
| 11663 | 2026-08-17T05:54:51.790Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a66b2f6b14d25aac; input_fingerprint=3ea5a66214a15704a05883a60a07b51a8c2ccca29162b3e444d79dc538da8eb7 |
| 11664 | 2026-08-17T05:54:52.197Z | managed_process_admitted |  |  | owner=default |
| 11665 | 2026-08-17T05:54:52.541Z | managed_process_started |  |  | owner=default |
| 11666 | 2026-08-17T05:54:53.127Z | managed_process_terminal |  |  | owner=default |
| 11667 | 2026-08-17T05:54:53.448Z | proof_recorded |  |  | stage_id=check:a66b2f6b14d25aac; status=passed; cache_hit=False; input_fingerprint=3ea5a66214a15704a05883a60a07b51a8c2ccca29162b3e444d79dc538da8eb7 |
| 11668 | 2026-08-17T05:54:53.629Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:90447173833573ac; input_fingerprint=b58946c62e0267372dbed48a7c02aabc70e820b4e55537be055877d6b0b99010 |
| 11669 | 2026-08-17T05:54:53.971Z | managed_process_admitted |  |  | owner=default |
| 11670 | 2026-08-17T05:54:54.458Z | managed_process_started |  |  | owner=default |
| 11671 | 2026-08-17T05:55:15.172Z | managed_process_terminal |  |  | owner=default |
| 11672 | 2026-08-17T05:55:15.527Z | proof_recorded |  |  | stage_id=check:90447173833573ac; status=passed; cache_hit=False; input_fingerprint=b58946c62e0267372dbed48a7c02aabc70e820b4e55537be055877d6b0b99010 |
| 11673 | 2026-08-17T05:55:16.041Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11674 | 2026-08-17T05:55:35.074Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11675 | 2026-08-17T05:55:35.490Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7461bc5dce821b50 | passed | b09d4cbc57ab29dda1ff4e218a90b5fc9fc3bde78855bc86288a8cb5c901090d | False | 1416 | 0 |
| check:a66b2f6b14d25aac | passed | 3ea5a66214a15704a05883a60a07b51a8c2ccca29162b3e444d79dc538da8eb7 | False | 1316 | 0 |
| check:90447173833573ac | passed | b58946c62e0267372dbed48a7c02aabc70e820b4e55537be055877d6b0b99010 | False | 21571 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2060411587d94c4d9a7861c9ae13f7fd | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 68d2cecea4550795b20d5bb95add5df9b5a0ed52b1d9640eed7be4d915402818 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `f4611263d7607f676b7ca3bade117ae3baaf1d743e4eb4db04784a74acbc9c8d`
