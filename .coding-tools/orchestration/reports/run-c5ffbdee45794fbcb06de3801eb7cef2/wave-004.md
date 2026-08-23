# Orchestration Wave 4

- Run: `c5ffbdee45794fbcb06de3801eb7cef2`
- Wave: `1227ed85d1a64c8f9817cfc083cca4d4`
- Objective: Close the remaining proof-integrity gap by requiring an explicit normal success-terminal lifecycle plus exit_code 0 at the shared command classifier and verify_build boundary. Preserve the already-proven prediction-wave P4 source-state repair and all P5 fail-closed gates.
- Objective revision: `4`
- Objective SHA-256: `3ef023c7565d031d2eaf986770b8fd9d71ce60d2f7a3f2d9bce659354c3284bc`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `db45f1a03a056d1fa6e1a53991aaa5e097a1cd58`
- Worktree fingerprint: `3946e7c387d8aa4a95037b62b8f10002f36a7ba55c4a2b22bccf39505bc11ca0`
- Contract fingerprint: `945ae6e8974a60e6ed53d07125bf1acce32ddeef9aeeba07d58de7d55479de5a`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28680 | 2026-08-23T10:03:46.888Z | wave_replanned |  | PREFLIGHT | reason=Final Acceptance found the prior patch reused a helper that still accepted empty lifecycle status with exit_code 0. The strategy now tightens the common helper itself and adds direct missing/running plus accepted-terminal regressions before rerunning the affected suites. |
| 28681 | 2026-08-23T10:03:47.771Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 28682 | 2026-08-23T10:03:47.931Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28683 | 2026-08-23T10:03:48.091Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28684 | 2026-08-23T10:03:48.270Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 28685 | 2026-08-23T10:03:48.451Z | state_transition | READY | ROUTED | reason=route_selected |
| 28686 | 2026-08-23T10:03:49.320Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=12580c0d36e14f15b0d9a3601a8bbcfa |
| 28687 | 2026-08-23T10:03:49.496Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28688 | 2026-08-23T10:03:50.440Z | patch_surface_observed |  |  |  |
| 28689 | 2026-08-23T10:03:50.713Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=12580c0d36e14f15b0d9a3601a8bbcfa |
| 28690 | 2026-08-23T10:03:50.892Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28691 | 2026-08-23T10:03:51.713Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:5f2ba3883f4e1a64; input_fingerprint=749c1610efb4c7ef607789904a47657efd1cb939f231afb877644cf6495db2b5 |
| 28692 | 2026-08-23T10:03:52.063Z | managed_process_admitted |  |  | owner=default |
| 28693 | 2026-08-23T10:03:52.390Z | managed_process_started |  |  | owner=default |
| 28694 | 2026-08-23T10:04:35.907Z | managed_process_terminal |  |  | owner=default |
| 28695 | 2026-08-23T10:04:36.267Z | proof_recorded |  |  | stage_id=check:5f2ba3883f4e1a64; status=failed; cache_hit=False; input_fingerprint=749c1610efb4c7ef607789904a47657efd1cb939f231afb877644cf6495db2b5 |
| 28696 | 2026-08-23T10:04:36.447Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 28697 | 2026-08-23T10:04:36.646Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 28698 | 2026-08-23T10:04:36.837Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5f2ba3883f4e1a64 | failed | 749c1610efb4c7ef607789904a47657efd1cb939f231afb877644cf6495db2b5 | False | 44214 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `122`
- Chain head: `f5d5313275888b2939cb1adf69d54d748815afc26313b27cb59e574bd0f3be47`
