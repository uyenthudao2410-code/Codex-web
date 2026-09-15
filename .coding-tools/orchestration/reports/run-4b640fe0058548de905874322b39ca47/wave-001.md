# Orchestration Wave 1

- Run: `4b640fe0058548de905874322b39ca47`
- Wave: `c1f5fcaafcad403b85838498ebe9bc7d`
- Objective: Fix the proven Recovery Supervisor optional-property regression that prevents sparse persisted status rehydration and makes install readiness consume defaults instead of real fields. Make the smallest causal source change in Get-OptionalProperty so missing properties return the supplied default and existing properties return their stored value. Add a focused regression proving an existing optional persisted value survives while missing fields safely default. Preserve all unrelated dirty bytes. Validate first with tests/recovery-supervisor.test.js only; do not reinstall or restart in this source-fix wave.
- Objective revision: `1`
- Objective SHA-256: `8e13ee13974f34b3445446195ac684208768c8b7869a30e928198d1ff206ef94`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `b7325226698fe70dc2b1460c2078bed2f064bdb513d1c77b938e0f5983bcb4b4`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57841 | 2026-09-15T07:37:29.545Z | run_started |  | PREFLIGHT |  |
| 57842 | 2026-09-15T07:37:30.597Z | observation_span_recorded |  |  |  |
| 57843 | 2026-09-15T07:37:31.032Z | solution_shadow_recommended |  |  |  |
| 57844 | 2026-09-15T07:37:37.112Z | observation_span_recorded |  |  |  |
| 57845 | 2026-09-15T07:37:37.597Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57850 | 2026-09-15T07:37:56.458Z | managed_process_admitted |  |  | owner=chatweb |
| 57851 | 2026-09-15T07:37:56.823Z | managed_process_started |  |  | owner=chatweb |
| 57852 | 2026-09-15T07:37:57.797Z | managed_process_terminal |  |  | owner=chatweb |
| 57854 | 2026-09-15T07:38:38.244Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57855 | 2026-09-15T07:38:38.453Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57856 | 2026-09-15T07:38:38.728Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57857 | 2026-09-15T07:38:38.954Z | state_transition | READY | ROUTED | reason=route_selected |
| 57858 | 2026-09-15T07:38:39.246Z | observation_span_recorded |  |  |  |
| 57859 | 2026-09-15T07:38:40.113Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=38013117f54241de9a729a018ce06c90 |
| 57860 | 2026-09-15T07:38:40.346Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57861 | 2026-09-15T07:38:41.186Z | observation_span_recorded |  |  |  |
| 57862 | 2026-09-15T07:38:41.622Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=38013117f54241de9a729a018ce06c90 |
| 57863 | 2026-09-15T07:38:41.833Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57864 | 2026-09-15T07:38:42.531Z | proof_cache_miss |  |  | reason=cold; stage_id=check:318bc57922f92423; input_fingerprint=4159286f2ad0143c1dcc1625c02d5fd1a76405a7160fb75d8c6efda9d0a8dc4b |
| 57865 | 2026-09-15T07:38:42.991Z | managed_process_admitted |  |  | owner=default |
| 57866 | 2026-09-15T07:38:43.416Z | managed_process_started |  |  | owner=default |
| 57867 | 2026-09-15T07:38:45.161Z | managed_process_terminal |  |  | owner=default |
| 57868 | 2026-09-15T07:38:45.740Z | proof_recorded |  |  | stage_id=check:318bc57922f92423; status=passed; cache_hit=False; input_fingerprint=4159286f2ad0143c1dcc1625c02d5fd1a76405a7160fb75d8c6efda9d0a8dc4b |
| 57869 | 2026-09-15T07:38:45.997Z | proof_cache_miss |  |  | reason=cold; stage_id=check:937c0f2c3d7f5d9e; input_fingerprint=dba9660db24cbab41ecfde767fb189e0da50a81857ea9422c563552255376a81 |
| 57870 | 2026-09-15T07:38:46.636Z | managed_process_admitted |  |  | owner=default |
| 57871 | 2026-09-15T07:38:46.990Z | managed_process_started |  |  | owner=default |
| 57872 | 2026-09-15T07:38:48.970Z | managed_process_terminal |  |  | owner=default |
| 57873 | 2026-09-15T07:38:49.374Z | proof_recorded |  |  | stage_id=check:937c0f2c3d7f5d9e; status=passed; cache_hit=False; input_fingerprint=dba9660db24cbab41ecfde767fb189e0da50a81857ea9422c563552255376a81 |
| 57874 | 2026-09-15T07:38:49.613Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=d4394d5d93d1663f6eb3947503135c1b15a73a19666c2d70ed97196729e1bf84 |
| 57875 | 2026-09-15T07:38:50.039Z | managed_process_admitted |  |  | owner=default |
| 57876 | 2026-09-15T07:38:50.456Z | managed_process_started |  |  | owner=default |
| 57877 | 2026-09-15T07:38:52.210Z | managed_process_terminal |  |  | owner=default |
| 57878 | 2026-09-15T07:38:54.036Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=d4394d5d93d1663f6eb3947503135c1b15a73a19666c2d70ed97196729e1bf84 |
| 57879 | 2026-09-15T07:38:54.483Z | observation_span_recorded |  |  |  |
| 57880 | 2026-09-15T07:38:54.945Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 57881 | 2026-09-15T07:38:55.175Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 57898 | 2026-09-15T07:40:11.735Z | quality_outcome_recorded |  |  |  |
| 57899 | 2026-09-15T07:40:11.925Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 57900 | 2026-09-15T07:40:12.342Z | observation_span_recorded |  |  |  |
| 57901 | 2026-09-15T07:40:12.600Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 57902 | 2026-09-15T07:40:12.829Z | observation_span_recorded |  |  |  |
| 57903 | 2026-09-15T07:40:13.087Z | observation_span_recorded |  |  |  |
| 57904 | 2026-09-15T07:40:13.329Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:318bc57922f92423 | passed | 4159286f2ad0143c1dcc1625c02d5fd1a76405a7160fb75d8c6efda9d0a8dc4b | False | 2628 | 0 |
| check:937c0f2c3d7f5d9e | passed | dba9660db24cbab41ecfde767fb189e0da50a81857ea9422c563552255376a81 | False | 2814 | 0 |
| verify:tests | passed | d4394d5d93d1663f6eb3947503135c1b15a73a19666c2d70ed97196729e1bf84 | False | 4000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| cc7de336a3cb4445b2d19b697918b8a7 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 65a778a842d3b100a28cd9b378d135a2586afe045116694e6b403b6062b75a2c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `678075fe1601f95b9d6432280ca1a30cc4d48a92486a98249640ec0db03dad5c`
