# Orchestration Wave 1

- Run: `02e761fa895d4e728d28d04182f2cedf`
- Wave: `7a0f8ffa3dfd473bbbcb791922503763`
- Objective: Apply TG1-TG12 Stage B V4 exact-write packet to the authoritative dirty workspace and prove changed behavior
- Objective revision: `1`
- Objective SHA-256: `c6c27efeac75b597e1360bddfedc0c9534eefcbb1fff629d86a30574faf3fa64`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `9a9114af87fabb22bdb388af4b201cabde995d56603d51af54c96f14c8db4750`
- Contract fingerprint: `6bc9eaf623ada4b15c77f2926eb17a49dbcdb1606c407afddc97b9115ba397c1`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36051 | 2026-09-03T04:34:07.607Z | run_started |  | PREFLIGHT |  |
| 36052 | 2026-09-03T04:34:07.995Z | patch_artifacts_loaded | PREFLIGHT | PREFLIGHT |  |
| 36053 | 2026-09-03T04:34:08.194Z | observation_span_recorded |  |  |  |
| 36054 | 2026-09-03T04:34:09.170Z | observation_span_recorded |  |  |  |
| 36055 | 2026-09-03T04:34:09.386Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36056 | 2026-09-03T04:34:09.593Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36057 | 2026-09-03T04:34:09.800Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36058 | 2026-09-03T04:34:09.994Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36059 | 2026-09-03T04:34:10.184Z | state_transition | READY | ROUTED | reason=route_selected |
| 36060 | 2026-09-03T04:34:10.413Z | observation_span_recorded |  |  |  |
| 36061 | 2026-09-03T04:34:11.526Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1165a7cb25304c029ddd73545bd256ed |
| 36062 | 2026-09-03T04:34:11.730Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36063 | 2026-09-03T04:34:14.707Z | patch_surface_observed |  |  |  |
| 36064 | 2026-09-03T04:34:14.904Z | observation_span_recorded |  |  |  |
| 36065 | 2026-09-03T04:34:15.207Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1165a7cb25304c029ddd73545bd256ed |
| 36066 | 2026-09-03T04:34:15.352Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36067 | 2026-09-03T04:34:16.458Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c8980b1bb9e98977; input_fingerprint=ee5ccab10315d6c4a507cdd3cbf63f90ca9f054140175fd73ee4f44cc1066a93 |
| 36068 | 2026-09-03T04:34:16.928Z | managed_process_admitted |  |  | owner=default |
| 36069 | 2026-09-03T04:34:17.262Z | managed_process_started |  |  | owner=default |
| 36070 | 2026-09-03T04:34:20.543Z | managed_process_terminal |  |  | owner=default |
| 36071 | 2026-09-03T04:34:21.157Z | proof_recorded |  |  | stage_id=check:c8980b1bb9e98977; status=failed; cache_hit=False; input_fingerprint=ee5ccab10315d6c4a507cdd3cbf63f90ca9f054140175fd73ee4f44cc1066a93 |
| 36072 | 2026-09-03T04:34:21.344Z | observation_span_recorded |  |  |  |
| 36073 | 2026-09-03T04:34:21.540Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 36074 | 2026-09-03T04:34:21.711Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 36075 | 2026-09-03T04:34:21.944Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:c8980b1bb9e98977 | failed | ee5ccab10315d6c4a507cdd3cbf63f90ca9f054140175fd73ee4f44cc1066a93 | False | 4054 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `222`
- Chain head: `acc5c5cbb29137c03d5a1a3cc7eb065d17c4bf71f5f9072787acf4f4896feb6c`
