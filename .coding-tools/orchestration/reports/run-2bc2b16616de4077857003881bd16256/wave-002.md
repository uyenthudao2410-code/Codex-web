# Orchestration Wave 2

- Run: `2bc2b16616de4077857003881bd16256`
- Wave: `2f965333e7da48b5bb5aab22ffe9c44e`
- Objective: C01/M02 machine-A packaged Recovery Supervisor transition for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Replan after the prior wave was blocked before mutation because controller-side localhost recovery.ping requires network permission that this client cannot elicit. Keep the same transition and rollback scope, but use the exact accepted Recovery Supervisor itself as the authenticated health oracle: its Install action starts the replacement task and Wait-InstalledSupervisorReady accepts only a fresh capability-bearing heartbeat after Invoke-Cycle; Invoke-Cycle marks healthy only after its internal authenticated recovery.ping succeeds. Controller postconditions therefore verify exact supervisor/source identity, manifest/status identity, Scheduled Task contract, live descriptor/process identity unchanged, status last_host_pid/last_host_instance_id equal the pre-transition descriptor, and last_spawned_pid null. Do not perform any direct controller network call. Transition from development to packaged mode using only the installed candidate supervisor script/executable. Roll back to the exact development supervisor if any mutation/postcondition fails. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy.
- Objective revision: `2`
- Objective SHA-256: `94b95b661766059cda65515379e5ea148ff86cd5764bf1421721e01790ccacf4`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58738 | 2026-09-15T09:08:08.698Z | wave_replanned |  | PREFLIGHT | reason=Previous wave ad40dc80d3f949c2b3d3cd32ae698bcd was blocked before mutation by NETWORK_PERMISSION_REQUIRED because the controller oracle attempted an explicit localhost HTTP recovery.ping. Permission elicitation is unsupported in this client. Change strategy: rely on the exact attested Recovery Supervisor's own authenticated Invoke-RecoveryPing/Wait-InstalledSupervisorReady path, and controller-side non-network process/descriptor/status/task/hash postconditions. No external state changed in the failed wave. |
| 58739 | 2026-09-15T09:08:09.144Z | observation_span_recorded |  |  |  |
| 58746 | 2026-09-15T09:08:56.403Z | observation_span_recorded |  |  |  |
| 58747 | 2026-09-15T09:08:56.943Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58754 | 2026-09-15T09:09:32.296Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58755 | 2026-09-15T09:09:32.500Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58756 | 2026-09-15T09:09:32.721Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58757 | 2026-09-15T09:09:33.066Z | state_transition | READY | ROUTED | reason=route_selected |
| 58758 | 2026-09-15T09:09:33.491Z | observation_span_recorded |  |  |  |
| 58759 | 2026-09-15T09:09:34.476Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1c30524966fc4fe5b843ccdddb193e1a |
| 58760 | 2026-09-15T09:09:35.058Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58761 | 2026-09-15T09:09:35.673Z | observation_span_recorded |  |  |  |
| 58762 | 2026-09-15T09:09:36.259Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1c30524966fc4fe5b843ccdddb193e1a |
| 58763 | 2026-09-15T09:09:36.553Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58764 | 2026-09-15T09:09:37.312Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bc1607f6927ae35f; input_fingerprint=fafdcd7e504d6e54592ddcc120a1feab8130c8adc2d0970255e7f2783470ce2e |
| 58765 | 2026-09-15T09:09:38.062Z | managed_process_admitted |  |  | owner=default |
| 58766 | 2026-09-15T09:09:38.674Z | managed_process_started |  |  | owner=default |
| 58767 | 2026-09-15T09:09:40.175Z | managed_process_terminal |  |  | owner=default |
| 58768 | 2026-09-15T09:09:41.162Z | proof_recorded |  |  | stage_id=check:bc1607f6927ae35f; status=failed; cache_hit=False; input_fingerprint=fafdcd7e504d6e54592ddcc120a1feab8130c8adc2d0970255e7f2783470ce2e |
| 58769 | 2026-09-15T09:09:41.650Z | observation_span_recorded |  |  |  |
| 58770 | 2026-09-15T09:09:41.934Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 58771 | 2026-09-15T09:09:42.239Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 58772 | 2026-09-15T09:09:42.577Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58792 | 2026-09-15T09:11:05.410Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:bc1607f6927ae35f | failed | fafdcd7e504d6e54592ddcc120a1feab8130c8adc2d0970255e7f2783470ce2e | False | 3003 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `a1b6c357935ccb198a60f090f208d3c0dbec36c62138d7762fa8ed0a545815c5`
