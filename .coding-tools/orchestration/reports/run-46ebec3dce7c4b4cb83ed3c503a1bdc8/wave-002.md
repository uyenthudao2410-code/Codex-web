# Orchestration Wave 2

- Run: `46ebec3dce7c4b4cb83ed3c503a1bdc8`
- Wave: `35e07b6c64fc4638ab0bb7cb145fd221`
- Objective: G2 corrective regression closure on current HEAD 8697ace8204e7e3da55d250d4a52d9b2b930116c: change only resources/coding-tools-mcp/tests/test_exception_group_boundary.py by adding self.task_state = SimpleNamespace(get=lambda: {}) inside FailingRuntime.__init__ for test_http_pre_dispatch_boundary_never_stringifies_exception_group. Preserve all concurrent WIP, keep production behavior unchanged, do not modify the two already-passing regression tests or any second path. Run focused three-test selection without pytest :: node IDs, then full npm test:all, module-size guard, git diff --check, and exact target-file diff inspection. Stop/replan on any drift or failed proof.
- Objective revision: `1`
- Objective SHA-256: `5d69d18bd4ed6b5c9506c73045b7f7ddca62a113ac1ef3a7dde43e4aa191cbdc`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `6cea96e7cef53cbcb5ddf5c275a7536101f4a046372fd0a36d6a7f232fc08429`
- Contract fingerprint: `0a1a837eee066d5098074c7ff2174c472d08a4b1c869a0fce2c21cdb1d685482`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39964 | 2026-09-04T12:01:55.509Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 focused three-regression proof passed. The full suite failed only in three recovery E2E harness cases outside the target: two EPERM temp-tree cleanup failures and one timeout waiting for recovery-host.json. Wave 2 changes strategy: adopt the exact unchanged G2 target byte without source mutation; rerun exactly those three retained failing recovery E2E tests first; only if they pass, rerun the focused three-regression selection, then the full suite and remaining guards on the settled current fingerprint. Do not reuse Wave 1 proof as current acceptance proof. |
| 39965 | 2026-09-04T12:01:55.722Z | observation_span_recorded |  |  |  |
| 39966 | 2026-09-04T12:01:55.964Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39967 | 2026-09-04T12:01:56.224Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39968 | 2026-09-04T12:01:56.407Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 39969 | 2026-09-04T12:01:56.587Z | state_transition | READY | ROUTED | reason=route_selected |
| 39970 | 2026-09-04T12:01:56.890Z | observation_span_recorded |  |  |  |
| 39971 | 2026-09-04T12:01:57.566Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=50cc47e47340496dbce2f3d4eb88e3b6 |
| 39972 | 2026-09-04T12:01:57.703Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39973 | 2026-09-04T12:01:58.142Z | existing_file_adoption_observed |  |  |  |
| 39974 | 2026-09-04T12:01:58.337Z | observation_span_recorded |  |  |  |
| 39975 | 2026-09-04T12:01:58.626Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=50cc47e47340496dbce2f3d4eb88e3b6 |
| 39976 | 2026-09-04T12:01:58.656Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39977 | 2026-09-04T12:01:59.123Z | proof_cache_miss |  |  | reason=cold; stage_id=check:61179c2f8b80c958; input_fingerprint=d402572869db8f4105028ac0411e0898f07df74ba7863e493f9f1768a91df2c9 |
| 39978 | 2026-09-04T12:01:59.572Z | managed_process_admitted |  |  | owner=default |
| 39979 | 2026-09-04T12:02:00.053Z | managed_process_started |  |  | owner=default |
| 39980 | 2026-09-04T12:02:16.746Z | managed_process_terminal |  |  | owner=default |
| 39981 | 2026-09-04T12:02:16.972Z | proof_recorded |  |  | stage_id=check:61179c2f8b80c958; status=passed; cache_hit=False; input_fingerprint=d402572869db8f4105028ac0411e0898f07df74ba7863e493f9f1768a91df2c9 |
| 39982 | 2026-09-04T12:02:17.226Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8f279add4b11d6dd; input_fingerprint=660e119337d7651f5fd9ec3ffa4864d76d7b08b11a26d57236da172deb93fcf4 |
| 39983 | 2026-09-04T12:02:17.677Z | managed_process_admitted |  |  | owner=default |
| 39984 | 2026-09-04T12:02:18.324Z | managed_process_started |  |  | owner=default |
| 39985 | 2026-09-04T12:02:22.732Z | managed_process_terminal |  |  | owner=default |
| 39986 | 2026-09-04T12:02:23.230Z | proof_recorded |  |  | stage_id=check:8f279add4b11d6dd; status=passed; cache_hit=False; input_fingerprint=660e119337d7651f5fd9ec3ffa4864d76d7b08b11a26d57236da172deb93fcf4 |
| 39987 | 2026-09-04T12:02:23.441Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9aa3e2aac3285acc; input_fingerprint=84fa3209e291dd3bc164d00e1d98dc2a0901a1a18d1a907ac9ebf653236a334d |
| 39988 | 2026-09-04T12:02:24.275Z | managed_process_admitted |  |  | owner=default |
| 39989 | 2026-09-04T12:02:24.571Z | managed_process_started |  |  | owner=default |
| 40046 | 2026-09-04T12:11:23.040Z | managed_process_terminal |  |  | owner=default |
| 40047 | 2026-09-04T12:11:23.393Z | proof_recorded |  |  | stage_id=check:9aa3e2aac3285acc; status=passed; cache_hit=False; input_fingerprint=84fa3209e291dd3bc164d00e1d98dc2a0901a1a18d1a907ac9ebf653236a334d |
| 40048 | 2026-09-04T12:11:23.577Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=294fab3104ef7e1388172a24fd2c747d9ceb23f21444a34b937fd13f7e6ffcb0 |
| 40049 | 2026-09-04T12:11:24.008Z | managed_process_admitted |  |  | owner=default |
| 40050 | 2026-09-04T12:11:24.566Z | managed_process_started |  |  | owner=default |
| 40051 | 2026-09-04T12:11:24.984Z | managed_process_terminal |  |  | owner=default |
| 40052 | 2026-09-04T12:11:25.326Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=294fab3104ef7e1388172a24fd2c747d9ceb23f21444a34b937fd13f7e6ffcb0 |
| 40053 | 2026-09-04T12:11:25.483Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=dda702c0b6f829a5af28b2944ad7aa4de8772b8e1343b08c47dd059acbc7480a |
| 40054 | 2026-09-04T12:11:25.985Z | managed_process_admitted |  |  | owner=default |
| 40055 | 2026-09-04T12:11:26.324Z | managed_process_started |  |  | owner=default |
| 40056 | 2026-09-04T12:11:27.508Z | managed_process_terminal |  |  | owner=default |
| 40057 | 2026-09-04T12:11:27.792Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=dda702c0b6f829a5af28b2944ad7aa4de8772b8e1343b08c47dd059acbc7480a |
| 40058 | 2026-09-04T12:11:27.958Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7c0a9b351b151400; input_fingerprint=da1179bb400681ab5ce80e5b721b0e0509d64ffc4fafb6437d377cf179b27889 |
| 40059 | 2026-09-04T12:11:28.353Z | managed_process_admitted |  |  | owner=default |
| 40060 | 2026-09-04T12:11:28.641Z | managed_process_started |  |  | owner=default |
| 40061 | 2026-09-04T12:11:29.141Z | managed_process_terminal |  |  | owner=default |
| 40062 | 2026-09-04T12:11:29.450Z | proof_recorded |  |  | stage_id=check:7c0a9b351b151400; status=passed; cache_hit=False; input_fingerprint=da1179bb400681ab5ce80e5b721b0e0509d64ffc4fafb6437d377cf179b27889 |
| 40063 | 2026-09-04T12:11:29.643Z | observation_span_recorded |  |  |  |
| 40064 | 2026-09-04T12:11:29.688Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 40065 | 2026-09-04T12:15:28.296Z | observation_span_recorded |  |  |  |
| 40066 | 2026-09-04T12:15:28.474Z | failure_observed | ACCEPTING | ACCEPTING | reason=SOURCE_OR_STATE_DRIFT_POST_PROOF_6CEA96E7_TO_010F1467_TARGET_UNCHANGED; failure_class=SOL_REJECTED |
| 40067 | 2026-09-04T12:15:28.641Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 40068 | 2026-09-04T12:15:28.836Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:61179c2f8b80c958 | passed | d402572869db8f4105028ac0411e0898f07df74ba7863e493f9f1768a91df2c9 | False | 17456 | 0 |
| check:8f279add4b11d6dd | passed | 660e119337d7651f5fd9ec3ffa4864d76d7b08b11a26d57236da172deb93fcf4 | False | 5492 | 0 |
| check:9aa3e2aac3285acc | passed | 84fa3209e291dd3bc164d00e1d98dc2a0901a1a18d1a907ac9ebf653236a334d | False | 539597 | 0 |
| check:80a1a46bd01d26a3 | passed | 294fab3104ef7e1388172a24fd2c747d9ceb23f21444a34b937fd13f7e6ffcb0 | False | 1388 | 0 |
| check:466c2f308b48c766 | passed | dda702c0b6f829a5af28b2944ad7aa4de8772b8e1343b08c47dd059acbc7480a | False | 1997 | 0 |
| check:7c0a9b351b151400 | passed | da1179bb400681ab5ce80e5b721b0e0509d64ffc4fafb6437d377cf179b27889 | False | 1158 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `183`
- Chain head: `caab9385981a9d5463256d69b81b22c011156d1dfafcff04b6eee2cce6d10fc2`
