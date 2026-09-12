# Orchestration Wave 1

- Run: `d07cc568e2b345bb946754e565a026df`
- Wave: `32d4b12f908e45029b412f29eb599cf4`
- Objective: Implement Natural #4 exactly: add an opt-in CLI flag --stale-details to the empirical readiness reporter. Default output must remain backward-compatible and compact. When requested, stale_run_audit must include a bounded detail row for every THRESHOLD_SENSITIVE_STALE_CANDIDATE, including both over-threshold and below-threshold candidates, with run_id, activity_age_seconds, meets_current_stale_threshold boolean, latest_state_after, evidence-based subtype via the existing _stale_subtype logic, and last_event. Keep existing sample behavior unchanged. Add focused tests proving default omission/backward compatibility, full candidate coverage including a below-threshold candidate, reuse of existing subtype semantics, and unchanged read-only/no-reconciliation/no-P5 contract. Modify only the two authorized files and preserve unrelated WIP.
- Objective revision: `1`
- Objective SHA-256: `81b5c7cb57b3593ccb589270961ff33fc383ba6f7dd65f83d86f8c272c453957`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `5c4ef280d73a18ebbe2a9cf36edc8ac24f46ba285b23ba3f81e0ff8bc9ae08bc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45387 | 2026-09-09T09:33:06.629Z | run_started |  | PREFLIGHT |  |
| 45388 | 2026-09-09T09:33:07.203Z | observation_span_recorded |  |  |  |
| 45389 | 2026-09-09T09:33:07.492Z | solution_shadow_recommended |  |  |  |
| 45390 | 2026-09-09T09:33:12.892Z | observation_span_recorded |  |  |  |
| 45391 | 2026-09-09T09:33:13.160Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45392 | 2026-09-09T09:33:13.508Z | managed_process_admitted |  |  | owner=default |
| 45393 | 2026-09-09T09:33:13.825Z | managed_process_started |  |  | owner=default |
| 45394 | 2026-09-09T09:33:15.109Z | managed_process_terminal |  |  | owner=default |
| 45395 | 2026-09-09T09:33:15.392Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 45396 | 2026-09-09T09:33:15.576Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45397 | 2026-09-09T09:33:15.742Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45398 | 2026-09-09T09:33:15.959Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 45399 | 2026-09-09T09:33:16.110Z | state_transition | READY | ROUTED | reason=route_selected |
| 45400 | 2026-09-09T09:33:16.330Z | observation_span_recorded |  |  |  |
| 45401 | 2026-09-09T09:33:17.218Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d0f9663fb4384730bb577c1a2300fd11 |
| 45402 | 2026-09-09T09:33:17.397Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45403 | 2026-09-09T09:33:18.114Z | observation_span_recorded |  |  |  |
| 45404 | 2026-09-09T09:33:18.449Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d0f9663fb4384730bb577c1a2300fd11 |
| 45405 | 2026-09-09T09:33:18.619Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45406 | 2026-09-09T09:33:19.361Z | proof_cache_miss |  |  | reason=cold; stage_id=check:282ba5486f185742; input_fingerprint=59c79a843aac7fee4b79da6675c98d688e095970c47ea4321f7e934c4cb10099 |
| 45407 | 2026-09-09T09:33:19.710Z | managed_process_admitted |  |  | owner=default |
| 45408 | 2026-09-09T09:33:19.954Z | managed_process_started |  |  | owner=default |
| 45409 | 2026-09-09T09:33:20.358Z | managed_process_terminal |  |  | owner=default |
| 45410 | 2026-09-09T09:33:20.775Z | proof_recorded |  |  | stage_id=check:282ba5486f185742; status=failed; cache_hit=False; input_fingerprint=59c79a843aac7fee4b79da6675c98d688e095970c47ea4321f7e934c4cb10099 |
| 45411 | 2026-09-09T09:33:20.992Z | observation_span_recorded |  |  |  |
| 45412 | 2026-09-09T09:33:21.159Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 45413 | 2026-09-09T09:33:21.318Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 45414 | 2026-09-09T09:33:21.643Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:282ba5486f185742 | failed | 59c79a843aac7fee4b79da6675c98d688e095970c47ea4321f7e934c4cb10099 | False | 1051 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `52`
- Chain head: `9751cfcb51059e1597b201c5980931e31bd34ea2e1fe3f3dfad9bd871fc61c61`
