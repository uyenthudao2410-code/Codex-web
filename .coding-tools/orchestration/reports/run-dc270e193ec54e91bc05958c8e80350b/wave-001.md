# Orchestration Wave 1

- Run: `dc270e193ec54e91bc05958c8e80350b`
- Wave: `03fb3d68da574d838a9b7e86d51fc589`
- Objective: Fix Codex-web realtime performance card with exact rolling 5-minute provider-measured TPM and exact rolling 5-minute command latency, explicit freshness/no-data states, no stale hourly/daily/all-history fallbacks, no backend/public-tool changes, and focused renderer tests only. Preserve unrelated work. No restart, commit, push, or deploy.
- Mode: `mcp_only`
- Base HEAD: `359a5f231e1950e8d97303e0d2b798984c145fe6`
- Worktree fingerprint: `c9fa1642e156a5537872a25d2f38eaf288b2abdcac4ac02e3f30bd48ad309989`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20380 | 2026-08-19T06:24:47.877Z | run_started |  | PREFLIGHT |  |
| 20381 | 2026-08-19T06:24:48.754Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20382 | 2026-08-19T06:24:59.454Z | solution_shadow_recommended |  |  |  |
| 20383 | 2026-08-19T06:25:27.210Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20384 | 2026-08-19T06:25:27.340Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20385 | 2026-08-19T06:25:27.462Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20386 | 2026-08-19T06:25:27.647Z | state_transition | READY | ROUTED | reason=route_selected |
| 20387 | 2026-08-19T06:25:28.059Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=66934763ebcd42bc921511f744c945bb |
| 20388 | 2026-08-19T06:25:28.210Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20389 | 2026-08-19T06:25:28.676Z | patch_surface_observed |  |  |  |
| 20390 | 2026-08-19T06:25:28.938Z | patch_surface_observed |  |  |  |
| 20391 | 2026-08-19T06:25:29.185Z | patch_surface_observed |  |  |  |
| 20392 | 2026-08-19T06:25:29.427Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=66934763ebcd42bc921511f744c945bb |
| 20393 | 2026-08-19T06:25:29.576Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20394 | 2026-08-19T06:25:29.747Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 20395 | 2026-08-19T06:25:30.109Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 20396 | 2026-08-19T06:25:30.124Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=02a4877c5e0d319ba740557e35a2e2ebfc3d2aa78ab96708bc02ca53e2d8264f |
| 20397 | 2026-08-19T06:25:30.602Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 20398 | 2026-08-19T06:25:30.610Z | failure_observed | PROVING | PROVING | failure_class=EXECUTION_OWNER_INVALID |
| 20399 | 2026-08-19T06:25:30.940Z | state_transition | PROVING | REPLAN | reason=EXECUTION_OWNER_INVALID; failure_class=EXECUTION_OWNER_INVALID |
| 20400 | 2026-08-19T06:25:31.225Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `7bb72582b4d1641514c1889e5f705c74c30920a5dc299dba1e19352d6b079a8d`
