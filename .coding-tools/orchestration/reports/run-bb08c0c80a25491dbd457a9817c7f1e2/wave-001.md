# Orchestration Wave 1

- Run: `bb08c0c80a25491dbd457a9817c7f1e2`
- Wave: `5a63cd744ad54b71bee4f3b928ae7196`
- Objective: T2.1 TruthSnapshot integration bugfix only: fix the authenticated orchestration snapshot crash caused by passing unsupported keyword `wave=` into `OrchestrationLedger.wave_objective_provenance()`, whose accepted API takes `wave_id`. Change only that call-site and strengthen test_truth_snapshot with an active-wave regression that executes the same helper path. No other behavior, public tools, authority, UI, restart, package, release, or deployment changes.
- Objective revision: `1`
- Objective SHA-256: `19d09f5776c9479964f1dae0ffe82ff3c9afe588f1123bd6ce8d913d50d30fe3`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `e098d0c049a13ad0fcef97a4023c2fc7e5cb7fb16a0bdc66d90d39f4ff8dda9b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26248 | 2026-08-21T08:01:23.838Z | run_started |  | PREFLIGHT |  |
| 26249 | 2026-08-21T08:01:24.761Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26250 | 2026-08-21T08:01:45.623Z | solution_shadow_recommended |  |  |  |
| 26251 | 2026-08-21T08:02:12.866Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26252 | 2026-08-21T08:02:13.069Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26253 | 2026-08-21T08:02:13.248Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26254 | 2026-08-21T08:02:13.397Z | state_transition | READY | ROUTED | reason=route_selected |
| 26255 | 2026-08-21T08:02:13.819Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ba7cec3807de41f38fce6554e3fa133e |
| 26256 | 2026-08-21T08:02:13.988Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26257 | 2026-08-21T08:02:14.373Z | patch_surface_observed |  |  |  |
| 26258 | 2026-08-21T08:02:14.656Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ba7cec3807de41f38fce6554e3fa133e |
| 26259 | 2026-08-21T08:02:14.819Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26260 | 2026-08-21T08:02:15.156Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=8cdc70b762ee1022142f66b597739e83203d8608c3e6c15a352c7c8809060438 |
| 26261 | 2026-08-21T08:02:15.545Z | managed_process_admitted |  |  | owner=default |
| 26262 | 2026-08-21T08:02:15.891Z | managed_process_started |  |  | owner=default |
| 26263 | 2026-08-21T08:02:25.006Z | managed_process_terminal |  |  | owner=default |
| 26264 | 2026-08-21T08:02:25.381Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=8cdc70b762ee1022142f66b597739e83203d8608c3e6c15a352c7c8809060438 |
| 26265 | 2026-08-21T08:02:25.622Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 26266 | 2026-08-21T08:02:25.793Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 26267 | 2026-08-21T08:02:25.960Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 8cdc70b762ee1022142f66b597739e83203d8608c3e6c15a352c7c8809060438 | False | 9858 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `9477966f921405f9a6f7493d1814c9cfbaba5cf0bbe0004dc9a6729b012a8a9d`
