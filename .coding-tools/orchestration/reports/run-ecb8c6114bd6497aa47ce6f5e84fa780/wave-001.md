# Orchestration Wave 1

- Run: `ecb8c6114bd6497aa47ce6f5e84fa780`
- Wave: `eefc74b46b86435eaafdb3de5e377ff1`
- Objective: Implement the smallest fail-closed repair for post-activation exact-RUN stateless continuity. Change resolve_stateless_task_context so it reports request-scoped provenance only when an omitted task_context_id is successfully resolved from an exact ChatWeb task_control run selector; thread that provenance through MCPHandler into Runtime.request_context for the current request and clear it in finally; then in task_control allow _reconcile_task_orchestration_projection(requested_run_id=...) not only for action=get but also when the request-scoped exact-recovery provenance exactly equals the requested run_id. Direct historical audit/runtime calls without this provenance must keep their current semantics and must not rehydrate or replace the current operator-report latch. Explicit task_context_id calls must not be treated as transport recovery. Preserve all existing fail-closed projection_rebuild guards. Add a focused stateless HTTP regression: an archived canonical run whose context is polluted by a safely terminal duplicate must be recoverable by run-id-only task_control audit, must return/persist canonical TaskState in the exact recovered context, and the existing historical-audit operator-report isolation test must remain green. Do not touch W4 instrumentation or any unrelated source. No restart/commit/push/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `c73eae58957059b2d45ca5489ba37f9c86a70ae31af276e6252ec929e1b40606`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `db9f1f472815d07791ce1199f13a9b805aa4fd71ed82c5e6ebbe036ac0ba7e57`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34294 | 2026-09-01T07:27:19.395Z | run_started |  | PREFLIGHT |  |
| 34295 | 2026-09-01T07:27:19.711Z | observation_span_recorded |  |  |  |
| 34296 | 2026-09-01T07:27:19.919Z | solution_shadow_recommended |  |  |  |
| 34297 | 2026-09-01T07:27:20.122Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34298 | 2026-09-01T07:27:20.341Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34299 | 2026-09-01T07:27:20.541Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 34300 | 2026-09-01T07:27:20.741Z | state_transition | READY | ROUTED | reason=route_selected |
| 34301 | 2026-09-01T07:27:20.939Z | observation_span_recorded |  |  |  |
| 34302 | 2026-09-01T07:27:21.700Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=71e08efe81e6418ab7cd6b630f4e2ca5 |
| 34303 | 2026-09-01T07:27:21.924Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34304 | 2026-09-01T07:27:22.667Z | observation_span_recorded |  |  |  |
| 34305 | 2026-09-01T07:27:23.025Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=71e08efe81e6418ab7cd6b630f4e2ca5 |
| 34306 | 2026-09-01T07:27:23.242Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34307 | 2026-09-01T07:27:24.034Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=4f4381baf406f995b925077e790de6a685d456003a1f7bbd6562e8338e60b617 |
| 34308 | 2026-09-01T07:27:24.467Z | managed_process_admitted |  |  | owner=default |
| 34309 | 2026-09-01T07:27:24.909Z | managed_process_started |  |  | owner=default |
| 34310 | 2026-09-01T07:27:53.668Z | managed_process_terminal |  |  | owner=default |
| 34311 | 2026-09-01T07:27:53.991Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=4f4381baf406f995b925077e790de6a685d456003a1f7bbd6562e8338e60b617 |
| 34312 | 2026-09-01T07:27:54.184Z | observation_span_recorded |  |  |  |
| 34313 | 2026-09-01T07:27:54.433Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 34314 | 2026-09-01T07:28:18.285Z | observation_span_recorded |  |  |  |
| 34315 | 2026-09-01T07:28:18.458Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject no-change wave: proof only reran existing tests, affected_files/modified_files are empty, so it does not prove the exact-run stateless continuity defect was repaired. Replan on the same bugfix RUN with an actual bounded source patch and focused regression; preserve W4 untouched.; failure_class=SOL_REJECTED |
| 34316 | 2026-09-01T07:28:18.596Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 34317 | 2026-09-01T07:28:18.753Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 4f4381baf406f995b925077e790de6a685d456003a1f7bbd6562e8338e60b617 | False | 29577 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `739e6f214d313055fe14e8a2276cf2537f5f2479535fd571bccb90380d729b5d`
