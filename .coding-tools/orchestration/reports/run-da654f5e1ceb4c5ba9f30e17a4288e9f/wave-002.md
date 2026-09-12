# Orchestration Wave 2

- Run: `da654f5e1ceb4c5ba9f30e17a4288e9f`
- Wave: `7bcdd617df854d3886452c4d99226f98`
- Objective: Continue the same RUN for Problem prl-terminal-projection-clear-restart-drift-20260912 after wave 1 made no source changes and failed only because one proposed test path did not exist. Re-localize using only files that actually exist. Determine the exact classification path that turns a durable terminal accepted/checkpointed RUN into TERMINAL_PARENT_CONTRADICTION / missing projection after request-scoped task clear, identify the smallest source change, and identify existing test module(s) where the regression belongs. Do not mutate source or restart runtime in this prepare wave.
- Objective revision: `2`
- Objective SHA-256: `75b8293c836e478eec3f6fb32b34c9b58e6e20e4940253dae777c5657087b009`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `3afc90dfca1133e4e987b4a279b1fedc0532b5ce46323facea6689e31dbcf716`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 51060 | 2026-09-12T09:24:43.170Z | wave_replanned |  | PREFLIGHT | reason=ORACLE_PATH_CORRECTION_ONLY: prior wave changed no source and failed before implementation because tests/test_lifecycle_contextual_projection.py does not exist. Re-localize against existing source/tests before any write; do not reuse the invalid verification command. |
| 51061 | 2026-09-12T09:24:43.460Z | observation_span_recorded |  |  |  |
| 51062 | 2026-09-12T09:24:48.938Z | observation_span_recorded |  |  |  |
| 51063 | 2026-09-12T09:24:49.146Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 51064 | 2026-09-12T09:25:46.103Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 51065 | 2026-09-12T09:25:46.294Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 51066 | 2026-09-12T09:25:46.552Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 51067 | 2026-09-12T09:25:47.093Z | state_transition | READY | ROUTED | reason=route_selected |
| 51068 | 2026-09-12T09:25:47.351Z | observation_span_recorded |  |  |  |
| 51069 | 2026-09-12T09:25:48.314Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b2d28e8d3863494f9c1ca7c36bffb951 |
| 51070 | 2026-09-12T09:25:48.556Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 51071 | 2026-09-12T09:25:49.468Z | observation_span_recorded |  |  |  |
| 51072 | 2026-09-12T09:25:49.819Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b2d28e8d3863494f9c1ca7c36bffb951 |
| 51073 | 2026-09-12T09:25:50.010Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 51074 | 2026-09-12T09:25:50.843Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=8709587e04cb4a384c4553ccfc596740bfdecaf676fd16cffb67f98cdc4ab1c5 |
| 51075 | 2026-09-12T09:25:51.235Z | managed_process_admitted |  |  | owner=default |
| 51076 | 2026-09-12T09:25:51.635Z | managed_process_started |  |  | owner=default |
| 51077 | 2026-09-12T09:26:01.749Z | managed_process_terminal |  |  | owner=default |
| 51078 | 2026-09-12T09:26:02.172Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=8709587e04cb4a384c4553ccfc596740bfdecaf676fd16cffb67f98cdc4ab1c5 |
| 51079 | 2026-09-12T09:26:02.399Z | observation_span_recorded |  |  |  |
| 51080 | 2026-09-12T09:26:02.604Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 51081 | 2026-09-12T09:26:02.826Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 51082 | 2026-09-12T09:26:15.114Z | observation_span_recorded |  |  |  |
| 51083 | 2026-09-12T09:26:15.504Z | failure_observed | ACCEPTING | ACCEPTING | reason=NO_DURABLE_SOURCE_CHANGE: verification passed only against the pre-existing test suite, but affected_files and adopted_files are empty. The Problem requires an actual causal projection fix plus focused regression. Replan with exact source localization and require durable file receipts before acceptance.; failure_class=SOL_REJECTED |
| 51084 | 2026-09-12T09:26:15.736Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 51085 | 2026-09-12T09:26:15.959Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 8709587e04cb4a384c4553ccfc596740bfdecaf676fd16cffb67f98cdc4ab1c5 | False | 10920 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `78f1bf7f5a22897532a8058da664ee7ec58fa37f3f8e1357d28efa4425ced6ee`
