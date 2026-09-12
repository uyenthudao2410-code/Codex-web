# Orchestration Wave 1

- Run: `f240ecad2d7f42b58c0d087cf409d5c3`
- Wave: `1c641d5bcf224a4ea3428abfa44421bd`
- Objective: Fix the remaining stage-latency reporter cohort/binding defect for Problem prl-8a57cc01ad8abd9f56a14c8bd605229d revision 1. Canonical live ledger already proves a post-activation accepted natural RUN e94e9cadac0b40708f2274fa24ec28fb / wave 19d9574db27547faa36ed20e6af3a1a2 emitted an acceptance anchor plus same-clock controller_processing and acceptance_wait spans, yet report_stage_latency_attribution with explicit source_head 7bc1caee37107a15e74eb078b52fe314e5fa33ab reports accepted_current_source_runs=0, observed_runs=0, source_head_used_for_current_cohort=null, and HOST_BINDING_COVERAGE_BELOW_THRESHOLD. Diagnose the exact consumer selection/binding cause and prepare the smallest fail-closed fix so explicit immutable source_head can select matching latest waves even on a dirty worktree, while host binding remains exact and missing evidence remains unknown. Do not weaken the 0.9 host-binding threshold, do not infer by timestamp proximity, do not backfill history, do not touch workflow_tools.py, and do not change EOCL/Problem authority.
- Objective revision: `1`
- Objective SHA-256: `5b30688604fa9114455cb1f57250b1fb73734827f0344d72c7848a1cc2d5e1bc`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `12a01feb6f3f58e34b33571a52e4c426d4bd3a1e0ed1df5765cf9c47c2a06d18`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50402 | 2026-09-12T06:48:29.261Z | run_started |  | PREFLIGHT |  |
| 50403 | 2026-09-12T06:48:29.841Z | observation_span_recorded |  |  |  |
| 50404 | 2026-09-12T06:48:30.042Z | solution_shadow_recommended |  |  |  |
| 50405 | 2026-09-12T06:48:35.470Z | observation_span_recorded |  |  |  |
| 50406 | 2026-09-12T06:48:35.640Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50407 | 2026-09-12T06:49:03.767Z | managed_process_admitted |  |  | owner=default |
| 50408 | 2026-09-12T06:49:04.142Z | managed_process_started |  |  | owner=default |
| 50409 | 2026-09-12T06:49:04.659Z | managed_process_terminal |  |  | owner=default |
| 50410 | 2026-09-12T06:49:59.939Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50411 | 2026-09-12T06:50:00.114Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50412 | 2026-09-12T06:50:00.359Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 50413 | 2026-09-12T06:50:00.557Z | state_transition | READY | ROUTED | reason=route_selected |
| 50414 | 2026-09-12T06:50:00.776Z | observation_span_recorded |  |  |  |
| 50415 | 2026-09-12T06:50:01.788Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5fdbd4b5dda74ed7b0132685076fd80b |
| 50416 | 2026-09-12T06:50:01.990Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50417 | 2026-09-12T06:50:02.911Z | patch_surface_observed |  |  |  |
| 50418 | 2026-09-12T06:50:03.139Z | observation_span_recorded |  |  |  |
| 50419 | 2026-09-12T06:50:03.437Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5fdbd4b5dda74ed7b0132685076fd80b |
| 50420 | 2026-09-12T06:50:03.644Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50421 | 2026-09-12T06:50:04.432Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1af669ec6b00ebdf; input_fingerprint=0db3a8bb6ed1526a7c21017cf0ab55cc6b6e2a3daf1d59fedb019434e7fb4c18 |
| 50422 | 2026-09-12T06:50:04.829Z | managed_process_admitted |  |  | owner=default |
| 50423 | 2026-09-12T06:50:05.156Z | managed_process_started |  |  | owner=default |
| 50424 | 2026-09-12T06:50:05.587Z | managed_process_terminal |  |  | owner=default |
| 50425 | 2026-09-12T06:50:06.055Z | proof_recorded |  |  | stage_id=check:1af669ec6b00ebdf; status=passed; cache_hit=False; input_fingerprint=0db3a8bb6ed1526a7c21017cf0ab55cc6b6e2a3daf1d59fedb019434e7fb4c18 |
| 50426 | 2026-09-12T06:50:06.270Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7b2904dd03d45b28; input_fingerprint=fec1293ddd97dfdd5aba5abc70404ce50d7948fb64a743f6e63f9892ad40fa4d |
| 50427 | 2026-09-12T06:50:06.650Z | managed_process_admitted |  |  | owner=default |
| 50428 | 2026-09-12T06:50:06.973Z | managed_process_started |  |  | owner=default |
| 50429 | 2026-09-12T06:50:09.896Z | managed_process_terminal |  |  | owner=default |
| 50430 | 2026-09-12T06:50:10.336Z | proof_recorded |  |  | stage_id=check:7b2904dd03d45b28; status=passed; cache_hit=False; input_fingerprint=fec1293ddd97dfdd5aba5abc70404ce50d7948fb64a743f6e63f9892ad40fa4d |
| 50431 | 2026-09-12T06:50:10.495Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=d63ff6ea614277ff2ef79cb51274ff72b1937471e5533ea35e8cf5f4ae58e8e7 |
| 50432 | 2026-09-12T06:50:10.886Z | managed_process_admitted |  |  | owner=default |
| 50433 | 2026-09-12T06:50:11.228Z | managed_process_started |  |  | owner=default |
| 50434 | 2026-09-12T06:50:21.570Z | managed_process_terminal |  |  | owner=default |
| 50435 | 2026-09-12T06:50:21.953Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=d63ff6ea614277ff2ef79cb51274ff72b1937471e5533ea35e8cf5f4ae58e8e7 |
| 50436 | 2026-09-12T06:50:23.041Z | observation_span_recorded |  |  |  |
| 50437 | 2026-09-12T06:50:23.241Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50438 | 2026-09-12T06:50:23.434Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 50439 | 2026-09-12T06:51:13.232Z | managed_process_admitted |  |  | owner=default |
| 50440 | 2026-09-12T06:51:13.600Z | managed_process_started |  |  | owner=default |
| 50441 | 2026-09-12T06:51:14.456Z | managed_process_terminal |  |  | owner=default |
| 50442 | 2026-09-12T06:51:28.814Z | quality_outcome_recorded |  |  |  |
| 50443 | 2026-09-12T06:51:28.978Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50444 | 2026-09-12T06:51:29.257Z | observation_span_recorded |  |  |  |
| 50445 | 2026-09-12T06:51:29.448Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 50446 | 2026-09-12T06:51:29.644Z | observation_span_recorded |  |  |  |
| 50447 | 2026-09-12T06:51:29.900Z | observation_span_recorded |  |  |  |
| 50448 | 2026-09-12T06:51:30.123Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1af669ec6b00ebdf | passed | 0db3a8bb6ed1526a7c21017cf0ab55cc6b6e2a3daf1d59fedb019434e7fb4c18 | False | 1157 | 0 |
| check:7b2904dd03d45b28 | passed | fec1293ddd97dfdd5aba5abc70404ce50d7948fb64a743f6e63f9892ad40fa4d | False | 3723 | 0 |
| verify:tests | passed | d63ff6ea614277ff2ef79cb51274ff72b1937471e5533ea35e8cf5f4ae58e8e7 | False | 11125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f80a3d0317474dbdb293488997238f21 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 066befe8dd4c3a0ad6f2f9381da71b814eaa284446df84b651c4354229043c61 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `1b1ae0ee55b106579f19ae5b1e2061f1568ce8bf8bbb216b20fec7703f964ef7`
