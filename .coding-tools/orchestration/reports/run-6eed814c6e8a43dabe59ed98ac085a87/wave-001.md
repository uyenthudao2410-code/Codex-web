# Orchestration Wave 1

- Run: `6eed814c6e8a43dabe59ed98ac085a87`
- Wave: `cf3a4dd9601c48d7913e81d157c34ef3`
- Objective: Run a fresh read-only exact stale-run maintenance preflight for the three previously scoped stale RUNs c9a67701e8554ce2b21e3117212797f6, 9c633d2185d84ed4b86fa60f6bfb38ef, 6559ba677eb742139c6f111e760edc78, and separately inspect 85aebc6dcb0d4cdbab3c1f91c813eae4. This diagnostic RUN exists only to give the read-only census commands canonical EOCL ownership so they do not appear as unbound live resources. Do not reconcile, mutate source, restart runtime, commit, push, clean, or reset. Preserve all dirty WIP. Report exact eligibility, live ownership, unbound resource residue, projection drift, integrity/FK status, and stale-threshold status for each target.
- Objective revision: `1`
- Objective SHA-256: `57de2a48201fb3e2e9b8398bd01ff4b990391c5df4ffa4e3048231e87bdd50e4`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `3afc90dfca1133e4e987b4a279b1fedc0532b5ce46323facea6689e31dbcf716`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50954 | 2026-09-12T09:16:40.860Z | run_started |  | PREFLIGHT |  |
| 50955 | 2026-09-12T09:16:41.746Z | observation_span_recorded |  |  |  |
| 50956 | 2026-09-12T09:16:42.907Z | observation_span_recorded |  |  |  |
| 50957 | 2026-09-12T09:16:43.120Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50958 | 2026-09-12T09:16:43.347Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 50959 | 2026-09-12T09:16:43.568Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50960 | 2026-09-12T09:16:43.757Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50961 | 2026-09-12T09:16:44.009Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 50962 | 2026-09-12T09:16:44.196Z | state_transition | READY | ROUTED | reason=route_selected |
| 50963 | 2026-09-12T09:16:44.402Z | observation_span_recorded |  |  |  |
| 50964 | 2026-09-12T09:16:45.558Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e4afcb9fb8db477082c3a5aed781ce3b |
| 50965 | 2026-09-12T09:16:45.839Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50966 | 2026-09-12T09:16:46.903Z | observation_span_recorded |  |  |  |
| 50967 | 2026-09-12T09:16:47.340Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e4afcb9fb8db477082c3a5aed781ce3b |
| 50968 | 2026-09-12T09:16:47.548Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50969 | 2026-09-12T09:16:48.462Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:38d71a711ab9a633; input_fingerprint=b13bdff6d087d59c700358d9e2785a3eed7deec48d27ed70f4abed7113cf7bb0 |
| 50970 | 2026-09-12T09:16:48.830Z | managed_process_admitted |  |  | owner=default |
| 50971 | 2026-09-12T09:16:49.145Z | managed_process_started |  |  | owner=default |
| 50972 | 2026-09-12T09:16:54.280Z | managed_process_terminal |  |  | owner=default |
| 50973 | 2026-09-12T09:16:54.780Z | proof_recorded |  |  | stage_id=check:38d71a711ab9a633; status=passed; cache_hit=False; input_fingerprint=b13bdff6d087d59c700358d9e2785a3eed7deec48d27ed70f4abed7113cf7bb0 |
| 50974 | 2026-09-12T09:16:54.997Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d71a5d8400a37add; input_fingerprint=2f6abcf3e3bea11119957a221ea4142e7480e3eedcb30a28bbd4fbbc04d8a89c |
| 50975 | 2026-09-12T09:16:55.440Z | managed_process_admitted |  |  | owner=default |
| 50976 | 2026-09-12T09:16:55.821Z | managed_process_started |  |  | owner=default |
| 50977 | 2026-09-12T09:17:00.979Z | managed_process_terminal |  |  | owner=default |
| 50978 | 2026-09-12T09:17:01.385Z | proof_recorded |  |  | stage_id=check:d71a5d8400a37add; status=passed; cache_hit=False; input_fingerprint=2f6abcf3e3bea11119957a221ea4142e7480e3eedcb30a28bbd4fbbc04d8a89c |
| 50979 | 2026-09-12T09:17:01.585Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:3a4ed2f0dfd33bca; input_fingerprint=8d85990d228b4ee85e904eccfd1cf618c3a77e28a5846c06a9a0123a964aa0a0 |
| 50980 | 2026-09-12T09:17:02.040Z | managed_process_admitted |  |  | owner=default |
| 50981 | 2026-09-12T09:17:02.406Z | managed_process_started |  |  | owner=default |
| 50982 | 2026-09-12T09:17:07.814Z | managed_process_terminal |  |  | owner=default |
| 50983 | 2026-09-12T09:17:08.214Z | proof_recorded |  |  | stage_id=check:3a4ed2f0dfd33bca; status=passed; cache_hit=False; input_fingerprint=8d85990d228b4ee85e904eccfd1cf618c3a77e28a5846c06a9a0123a964aa0a0 |
| 50984 | 2026-09-12T09:17:08.436Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8f32766ea3162a0a; input_fingerprint=b2c5335d81c816bf2e664d0d6b4b42701a76864667564ea0de2fe6ec398857e3 |
| 50985 | 2026-09-12T09:17:08.889Z | managed_process_admitted |  |  | owner=default |
| 50986 | 2026-09-12T09:17:09.289Z | managed_process_started |  |  | owner=default |
| 50987 | 2026-09-12T09:17:14.298Z | managed_process_terminal |  |  | owner=default |
| 50988 | 2026-09-12T09:17:14.814Z | proof_recorded |  |  | stage_id=check:8f32766ea3162a0a; status=failed; cache_hit=False; input_fingerprint=b2c5335d81c816bf2e664d0d6b4b42701a76864667564ea0de2fe6ec398857e3 |
| 50989 | 2026-09-12T09:17:15.037Z | observation_span_recorded |  |  |  |
| 50990 | 2026-09-12T09:17:15.284Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 50991 | 2026-09-12T09:17:15.517Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 50992 | 2026-09-12T09:17:15.751Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 50993 | 2026-09-12T09:18:06.036Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:38d71a711ab9a633 | passed | b13bdff6d087d59c700358d9e2785a3eed7deec48d27ed70f4abed7113cf7bb0 | False | 5862 | 0 |
| check:d71a5d8400a37add | passed | 2f6abcf3e3bea11119957a221ea4142e7480e3eedcb30a28bbd4fbbc04d8a89c | False | 5959 | 0 |
| check:3a4ed2f0dfd33bca | passed | 8d85990d228b4ee85e904eccfd1cf618c3a77e28a5846c06a9a0123a964aa0a0 | False | 6239 | 0 |
| check:8f32766ea3162a0a | failed | b2c5335d81c816bf2e664d0d6b4b42701a76864667564ea0de2fe6ec398857e3 | False | 5938 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `24610e000f9b361ec7f1a6294f97b13bd99c458acfd53904fbeddb0ea3502b8a`
