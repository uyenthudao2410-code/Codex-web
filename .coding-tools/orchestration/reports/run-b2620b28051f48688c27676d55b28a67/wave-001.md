# Orchestration Wave 1

- Run: `b2620b28051f48688c27676d55b28a67`
- Wave: `af46bf48ed8d4736bd82ed88cd56c764`
- Objective: Correct the PRL C4 full-claim mechanics canary so it measures actual immutable full_problem outcome claims, uses the canonical one-per-RUN exact primary Problem revision binding across replan waves, and preserves exact-wave manifest/proof/checkpoint/bridge verification. Add focused regressions for intent-only exclusion, valid replan claim coverage, and mismatched RUN binding failure. Do not backfill historical ledger data or modify schema/workflow producer semantics.
- Objective revision: `1`
- Objective SHA-256: `1172debd8d9d68cb682d551b01be60f372b6bf6debbb8864291dab97bfc521e2`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `027af408244ec5f2042ccce0f89dba13e1ce6087415305cc148f5970d6c1294a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50702 | 2026-09-12T07:57:01.991Z | run_started |  | PREFLIGHT |  |
| 50703 | 2026-09-12T07:57:02.802Z | observation_span_recorded |  |  |  |
| 50704 | 2026-09-12T07:57:03.031Z | solution_shadow_recommended |  |  |  |
| 50705 | 2026-09-12T07:57:03.808Z | observation_span_recorded |  |  |  |
| 50706 | 2026-09-12T07:57:03.999Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50707 | 2026-09-12T07:57:04.132Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50708 | 2026-09-12T07:57:04.306Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50709 | 2026-09-12T07:57:04.475Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 50710 | 2026-09-12T07:57:04.623Z | state_transition | READY | ROUTED | reason=route_selected |
| 50711 | 2026-09-12T07:57:04.790Z | observation_span_recorded |  |  |  |
| 50712 | 2026-09-12T07:57:05.699Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=94d3677bf1ba49d6be9361c51298caf5 |
| 50713 | 2026-09-12T07:57:05.846Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50714 | 2026-09-12T07:57:06.776Z | patch_surface_observed |  |  |  |
| 50715 | 2026-09-12T07:57:06.964Z | observation_span_recorded |  |  |  |
| 50716 | 2026-09-12T07:57:07.198Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=94d3677bf1ba49d6be9361c51298caf5 |
| 50717 | 2026-09-12T07:57:07.323Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50718 | 2026-09-12T07:57:08.134Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=8e817863442c82895b560b2c3c70f4bf116c21603908b6f74adf6adab1f7d116 |
| 50719 | 2026-09-12T07:57:08.840Z | managed_process_admitted |  |  | owner=default |
| 50720 | 2026-09-12T07:57:09.197Z | managed_process_started |  |  | owner=default |
| 50721 | 2026-09-12T07:57:18.564Z | managed_process_terminal |  |  | owner=default |
| 50722 | 2026-09-12T07:57:19.812Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=8e817863442c82895b560b2c3c70f4bf116c21603908b6f74adf6adab1f7d116 |
| 50723 | 2026-09-12T07:57:20.741Z | observation_span_recorded |  |  |  |
| 50724 | 2026-09-12T07:57:20.914Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50725 | 2026-09-12T07:57:21.057Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 50726 | 2026-09-12T08:05:36.531Z | managed_process_admitted |  |  | owner=default |
| 50727 | 2026-09-12T08:05:37.607Z | managed_process_started |  |  | owner=default |
| 50728 | 2026-09-12T08:05:38.538Z | managed_process_terminal |  |  | owner=default |
| 50729 | 2026-09-12T08:05:44.865Z | managed_process_admitted |  |  | owner=default |
| 50730 | 2026-09-12T08:05:45.304Z | managed_process_started |  |  | owner=default |
| 50731 | 2026-09-12T08:05:45.812Z | managed_process_terminal |  |  | owner=default |
| 50732 | 2026-09-12T08:05:53.163Z | managed_process_admitted |  |  | owner=default |
| 50733 | 2026-09-12T08:05:53.654Z | managed_process_started |  |  | owner=default |
| 50734 | 2026-09-12T08:05:54.222Z | managed_process_terminal |  |  | owner=default |
| 50735 | 2026-09-12T08:06:01.265Z | managed_process_admitted |  |  | owner=default |
| 50736 | 2026-09-12T08:06:01.782Z | managed_process_started |  |  | owner=default |
| 50737 | 2026-09-12T08:06:08.147Z | managed_process_terminal |  |  | owner=default |
| 50738 | 2026-09-12T08:06:17.340Z | managed_process_admitted |  |  | owner=default |
| 50739 | 2026-09-12T08:06:17.789Z | managed_process_started |  |  | owner=default |
| 50740 | 2026-09-12T08:06:18.336Z | managed_process_terminal |  |  | owner=default |
| 50741 | 2026-09-12T08:06:27.048Z | managed_process_admitted |  |  | owner=default |
| 50742 | 2026-09-12T08:06:27.415Z | managed_process_started |  |  | owner=default |
| 50743 | 2026-09-12T08:06:27.871Z | managed_process_terminal |  |  | owner=default |
| 50744 | 2026-09-12T08:06:49.691Z | quality_outcome_recorded |  |  |  |
| 50745 | 2026-09-12T08:06:49.860Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50746 | 2026-09-12T08:06:50.139Z | observation_span_recorded |  |  |  |
| 50747 | 2026-09-12T08:06:50.391Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 50748 | 2026-09-12T08:06:50.678Z | observation_span_recorded |  |  |  |
| 50749 | 2026-09-12T08:06:51.023Z | observation_span_recorded |  |  |  |
| 50750 | 2026-09-12T08:06:51.233Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 8e817863442c82895b560b2c3c70f4bf116c21603908b6f74adf6adab1f7d116 | False | 11062 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c9b6e72b9b434ddb880125bc6bf38847 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 703e55a4b504f32068d9f3201b47ba5212a68c62d010653dd8707b28d79e23c5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `49`
- Chain head: `b8e6914cf550cdca25107201de59b2e93f6e6ffb47f9443eeaeda5d4aa75dbf9`
