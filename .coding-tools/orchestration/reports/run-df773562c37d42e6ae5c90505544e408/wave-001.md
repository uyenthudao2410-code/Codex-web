# Orchestration Wave 1

- Run: `df773562c37d42e6ae5c90505544e408`
- Wave: `dfb052eeff2d4153b158b87d91607eca`
- Objective: Continue diagnosing the T2.1 integration failure now reproduced exactly: MCPHandler.control_orchestration_snapshot() returns truth_snapshot.orchestration.wave_id=None although the test created an active OrchestrationControl context and called task_state.set_orchestration_projection(ctx.projection()). Inspect only the reconciliation and task-state code that can clear/replace projection before truth snapshot construction. Identify the causal line and smallest correct fix/test adjustment. No mutation and no package/release/restart.
- Objective revision: `1`
- Objective SHA-256: `2ab9ea2dd5fe5ca4d3d4ce5c1d441bbc36fdc028d3e74ad92cdd1d1b676db1d4`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `87e50fccecdb18418e080235a97bea53a8178d724ef8c1eedfe1fa287a692e4f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26276 | 2026-08-21T08:18:06.788Z | run_started |  | PREFLIGHT |  |
| 26277 | 2026-08-21T08:18:07.599Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26278 | 2026-08-21T08:19:17.308Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26279 | 2026-08-21T08:19:17.468Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26280 | 2026-08-21T08:19:17.611Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26281 | 2026-08-21T08:19:17.826Z | state_transition | READY | ROUTED | reason=route_selected |
| 26282 | 2026-08-21T08:19:18.243Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2b8113b5e2ff483da93c315993a3d199 |
| 26283 | 2026-08-21T08:19:18.395Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26284 | 2026-08-21T08:19:18.761Z | patch_surface_observed |  |  |  |
| 26285 | 2026-08-21T08:19:18.980Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2b8113b5e2ff483da93c315993a3d199 |
| 26286 | 2026-08-21T08:19:19.159Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26287 | 2026-08-21T08:19:19.488Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3861e33657641ab1a65937d3c3e067ce21f049cffd17ee700715480b61a562b6 |
| 26288 | 2026-08-21T08:19:20.134Z | managed_process_admitted |  |  | owner=default |
| 26289 | 2026-08-21T08:19:20.420Z | managed_process_started |  |  | owner=default |
| 26290 | 2026-08-21T08:19:21.161Z | managed_process_terminal |  |  | owner=default |
| 26291 | 2026-08-21T08:19:22.564Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3861e33657641ab1a65937d3c3e067ce21f049cffd17ee700715480b61a562b6 |
| 26292 | 2026-08-21T08:19:23.043Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26293 | 2026-08-21T10:10:18.811Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject final acceptance because the wave's canonical effective_objective is the original diagnostic/no-mutation objective, but this same wave acquired a write lease and mutated resources/coding-tools-mcp/tests/test_truth_snapshot.py. Event replay contains no wave_replanned transition before mutation. This objective-to-mutation provenance mismatch violates T1 traceability. Replan a new wave with the exact T2.1 fixture-fix objective and rerun the focused TruthSnapshot oracle; do not modify production source.; failure_class=SOL_REJECTED |
| 26294 | 2026-08-21T10:10:19.014Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 26295 | 2026-08-21T10:10:19.223Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3861e33657641ab1a65937d3c3e067ce21f049cffd17ee700715480b61a562b6 | False | 2313 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `cae031e222add1786f2217b78666b443e10e361ea82faded7060bf45296cc28c`
