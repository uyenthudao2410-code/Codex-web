# Orchestration Wave 1

- Run: `fa3264abc45f44dfa780af1c697dd1d1`
- Wave: `170431c1d63e4e78ba9b8ad4cdd39d85`
- Objective: Fix the genuine webcodex-admin CLI validation bug where multiple bearer-token source selectors can be supplied together inconsistently. Before mutation, verify current behavior and the smallest causal scope: --token/--admin-token, --token-file, and --token-env/--admin-token-env must be mutually exclusive as alternative sources for the same bearer token; credential/credential-env are a separate fallback path and must not be conflated without evidence. Preserve all existing admin command semantics and proxy behavior. Add the smallest focused regression proving conflicts fail closed and a single token-env source remains valid. Do not touch unrelated source, do not commit/push, and do not manufacture a replan. This run is a genuine representative P4 bugfix sample.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `251f142746c8ff93e0e4d549ac320e35a3b6cf110e5ee261daf3c1a483c5d021`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18003 | 2026-08-18T15:34:28.831Z | run_started |  | PREFLIGHT |  |
| 18004 | 2026-08-18T15:34:33.966Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18005 | 2026-08-18T15:34:53.460Z | solution_shadow_recommended |  |  |  |
| 18006 | 2026-08-18T15:35:21.817Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 18007 | 2026-08-18T15:35:21.943Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 18008 | 2026-08-18T15:35:22.063Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 18009 | 2026-08-18T15:35:22.204Z | state_transition | READY | ROUTED | reason=route_selected |
| 18010 | 2026-08-18T15:35:22.650Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b77c3b2a011f4b8fbb7f50c28aa72ecf |
| 18011 | 2026-08-18T15:35:22.779Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 18012 | 2026-08-18T15:35:23.180Z | solution_shadow_patch_surface_observed |  |  |  |
| 18013 | 2026-08-18T15:35:23.354Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b77c3b2a011f4b8fbb7f50c28aa72ecf |
| 18014 | 2026-08-18T15:35:23.504Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 18015 | 2026-08-18T15:35:23.865Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e8e5ca9fe9e7664f; input_fingerprint=14918c3a26e774236af2ba11020b56b646ae5fbb30dbb87fe097857b9ba6433a |
| 18016 | 2026-08-18T15:35:24.165Z | managed_process_admitted |  |  | owner=default |
| 18017 | 2026-08-18T15:35:24.384Z | managed_process_started |  |  | owner=default |
| 18018 | 2026-08-18T15:35:25.059Z | managed_process_terminal |  |  | owner=default |
| 18019 | 2026-08-18T15:35:25.313Z | proof_recorded |  |  | stage_id=check:e8e5ca9fe9e7664f; status=passed; cache_hit=False; input_fingerprint=14918c3a26e774236af2ba11020b56b646ae5fbb30dbb87fe097857b9ba6433a |
| 18020 | 2026-08-18T15:35:25.454Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=80fec0d477b237d2e8e82d5aa526185e4473117337f506881fa492421a5d3db4 |
| 18021 | 2026-08-18T15:35:25.764Z | managed_process_admitted |  |  | owner=default |
| 18022 | 2026-08-18T15:35:25.982Z | managed_process_started |  |  | owner=default |
| 18023 | 2026-08-18T15:35:52.008Z | managed_process_terminal |  |  | owner=default |
| 18024 | 2026-08-18T15:35:53.064Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=80fec0d477b237d2e8e82d5aa526185e4473117337f506881fa492421a5d3db4 |
| 18025 | 2026-08-18T15:35:53.520Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 18026 | 2026-08-18T15:36:59.482Z | managed_process_admitted |  |  | owner=default |
| 18027 | 2026-08-18T15:36:59.741Z | managed_process_started |  |  | owner=default |
| 18028 | 2026-08-18T15:37:00.119Z | managed_process_terminal |  |  | owner=default |
| 18029 | 2026-08-18T15:37:13.529Z | managed_process_admitted |  |  | owner=default |
| 18030 | 2026-08-18T15:37:13.804Z | managed_process_started |  |  | owner=default |
| 18031 | 2026-08-18T15:37:14.229Z | managed_process_terminal |  |  | owner=default |
| 18032 | 2026-08-18T15:37:28.848Z | managed_process_admitted |  |  | owner=default |
| 18033 | 2026-08-18T15:37:29.075Z | managed_process_started |  |  | owner=default |
| 18034 | 2026-08-18T15:37:29.421Z | managed_process_terminal |  |  | owner=default |
| 18035 | 2026-08-18T15:39:00.762Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 18036 | 2026-08-18T15:39:01.028Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e8e5ca9fe9e7664f | passed | 14918c3a26e774236af2ba11020b56b646ae5fbb30dbb87fe097857b9ba6433a | False | 1216 | 0 |
| verify:tests | passed | 80fec0d477b237d2e8e82d5aa526185e4473117337f506881fa492421a5d3db4 | False | 27281 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 739873051f8146529f5c3fbdd70f2139 | accepted | b7af2598297870e816dd131b0f73e0f77d7608d5 | ae9f5035223553813cb956fc8a4a7aeac7cdec1d8c8c9167db57386f5d59af50 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `9d538302efef5e1053bea76d292230fd60bdb0ed7d2ffb417a15aa6ccb62bd60`
