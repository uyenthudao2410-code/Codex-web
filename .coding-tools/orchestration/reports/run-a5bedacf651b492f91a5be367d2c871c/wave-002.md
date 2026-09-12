# Orchestration Wave 2

- Run: `a5bedacf651b492f91a5be367d2c871c`
- Wave: `8e41b657c3af417ebeee6f83b831d882`
- Objective: Natural #9: fix the Manager Task page truthfulness/data bridge. Preserve bounded structured task evidence only when it belongs to the exact canonical displayed task/run; reject stale/hybrid detail on identity mismatch. Keep task history sourced from orchestration_ledger and preserve stateless/cross-context authority boundaries. Do not restart, commit, push, package, release, deploy, mutate P5, or reconcile stale runs.
- Objective revision: `2`
- Objective SHA-256: `9a2832dafaca5a74351e188929607437b0092bfea410a087096c8f5052a3b73a`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `9f658382e0403e9d1243bb94d6bd9a91ed18a4fecee451507c1b9ff1cf4184f6`
- Contract fingerprint: `c04fdc5e1ad20804ad3afad9465e6a9d6a91ac5339822bec7e2e933d6a352b1a`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45845 | 2026-09-09T13:18:07.893Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 source patch applied and diff check passed, but verification failed before exercising source because Python unittest was launched from the repository root and could not import coding_tools_mcp. Wave 2 changes the verification strategy: run Python from resources/coding-tools-mcp, run the Node bridge regression against the root test path, exact-byte adopt the existing four patched files, and do not replay the patch. |
| 45846 | 2026-09-09T13:18:08.044Z | observation_span_recorded |  |  |  |
| 45847 | 2026-09-09T13:18:13.813Z | observation_span_recorded |  |  |  |
| 45848 | 2026-09-09T13:18:14.147Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45849 | 2026-09-09T13:19:19.863Z | managed_process_admitted |  |  | owner=default |
| 45850 | 2026-09-09T13:19:20.255Z | managed_process_started |  |  | owner=default |
| 45851 | 2026-09-09T13:19:20.906Z | managed_process_terminal |  |  | owner=default |
| 45852 | 2026-09-09T13:19:50.709Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45853 | 2026-09-09T13:19:50.879Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45854 | 2026-09-09T13:19:51.047Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 45855 | 2026-09-09T13:19:51.205Z | state_transition | READY | ROUTED | reason=route_selected |
| 45856 | 2026-09-09T13:19:51.423Z | observation_span_recorded |  |  |  |
| 45857 | 2026-09-09T13:19:52.286Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=00bf644407f9400890004b4a86ae81fd |
| 45858 | 2026-09-09T13:19:52.480Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45859 | 2026-09-09T13:19:53.264Z | existing_file_adoption_observed |  |  |  |
| 45860 | 2026-09-09T13:19:53.469Z | observation_span_recorded |  |  |  |
| 45861 | 2026-09-09T13:19:53.760Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=00bf644407f9400890004b4a86ae81fd |
| 45862 | 2026-09-09T13:19:53.913Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45863 | 2026-09-09T13:19:54.619Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ec8d8b2c91d870cf; input_fingerprint=0b135faf3f9a545a64d6df97295208525ea29db2730834981a3f9c4db3776061 |
| 45864 | 2026-09-09T13:19:54.970Z | managed_process_admitted |  |  | owner=default |
| 45865 | 2026-09-09T13:19:55.288Z | managed_process_started |  |  | owner=default |
| 45866 | 2026-09-09T13:19:57.755Z | managed_process_terminal |  |  | owner=default |
| 45867 | 2026-09-09T13:19:58.144Z | proof_recorded |  |  | stage_id=check:ec8d8b2c91d870cf; status=failed; cache_hit=False; input_fingerprint=0b135faf3f9a545a64d6df97295208525ea29db2730834981a3f9c4db3776061 |
| 45868 | 2026-09-09T13:19:58.425Z | observation_span_recorded |  |  |  |
| 45869 | 2026-09-09T13:19:58.677Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 45870 | 2026-09-09T13:19:58.863Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 45871 | 2026-09-09T13:19:59.048Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ec8d8b2c91d870cf | failed | 0b135faf3f9a545a64d6df97295208525ea29db2730834981a3f9c4db3776061 | False | 3161 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `273`
- Chain head: `d882db9fd950ba73a7fd1fa1788fb65639608ff3522f81d5154eba3c07ab5251`
