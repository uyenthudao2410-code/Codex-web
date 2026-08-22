# Orchestration Wave 1

- Run: `4864f66b3f4c428c83f5ef0154140749`
- Wave: `b2f9c0ba80ef4783880cc78585aadf04`
- Objective: Implement the active canonical-ledger read-only path safety fix. Preserve all canonical project history. Add only a tiny shared read-only helper coding_tools_mcp/ledger_access.py that verifies workspace/.coding-tools/orchestration/ledger.sqlite3 exists before constructing OrchestrationLedger. Do not modify orchestration_ledger.py or Runtime creation behavior. Migrate read-only evaluation/report/benchmark paths to the helper. Make implicit CLI workspace defaults resolve to the repository root derived from script/module location; preserve every explicit --workspace value, temp/non-git workspace behavior through the normal constructor, and workspace switching. P5 baseline must preserve its existing LEDGER_MISSING reporting by avoiding ledger construction and passing empty organic_rework when readiness says LEDGER_MISSING. Add focused tests proving missing-ledger read-only reports/helper never create .coding-tools. Do not delete the existing nested DB yet. Do not commit/push/restart/change P5 state.
- Objective revision: `1`
- Objective SHA-256: `1476728fcf26ce5e9897bdd43905092462321a299b13fcedf420e8a0d4e6ac82`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0`
- Worktree fingerprint: `3f772125e2ee9ee0241440aa9afbe1fe02c393b08d367e8b1634999b9fc3b755`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27215 | 2026-08-22T14:03:29.016Z | run_started |  | PREFLIGHT |  |
| 27216 | 2026-08-22T14:03:49.504Z | solution_shadow_recommended |  |  |  |
| 27217 | 2026-08-22T14:04:10.987Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27218 | 2026-08-22T14:04:11.141Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27219 | 2026-08-22T14:04:11.279Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 27220 | 2026-08-22T14:04:11.405Z | state_transition | READY | ROUTED | reason=route_selected |
| 27221 | 2026-08-22T14:04:12.136Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5e594571d5ba4bb0a19d9dae4d038cc3 |
| 27222 | 2026-08-22T14:04:12.291Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27223 | 2026-08-22T14:04:13.056Z | patch_surface_observed |  |  |  |
| 27224 | 2026-08-22T14:04:13.319Z | patch_surface_observed |  |  |  |
| 27225 | 2026-08-22T14:04:13.542Z | patch_surface_observed |  |  |  |
| 27226 | 2026-08-22T14:04:13.837Z | patch_surface_observed |  |  |  |
| 27227 | 2026-08-22T14:04:14.103Z | patch_surface_observed |  |  |  |
| 27228 | 2026-08-22T14:04:14.370Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5e594571d5ba4bb0a19d9dae4d038cc3 |
| 27229 | 2026-08-22T14:04:14.540Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27230 | 2026-08-22T14:04:15.253Z | proof_cache_miss |  |  | reason=cold; stage_id=check:94ad7e02c6f989a4; input_fingerprint=b245e404759e4df22021402ca9c47862d713e0d4e47a2d39aa3cbd14ba304d30 |
| 27231 | 2026-08-22T14:04:15.675Z | managed_process_admitted |  |  | owner=default |
| 27232 | 2026-08-22T14:04:16.004Z | managed_process_started |  |  | owner=default |
| 27233 | 2026-08-22T14:04:16.388Z | managed_process_terminal |  |  | owner=default |
| 27234 | 2026-08-22T14:04:16.686Z | proof_recorded |  |  | stage_id=check:94ad7e02c6f989a4; status=failed; cache_hit=False; input_fingerprint=b245e404759e4df22021402ca9c47862d713e0d4e47a2d39aa3cbd14ba304d30 |
| 27235 | 2026-08-22T14:04:16.887Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 27236 | 2026-08-22T14:04:17.075Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 27237 | 2026-08-22T14:04:17.236Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:94ad7e02c6f989a4 | failed | b245e404759e4df22021402ca9c47862d713e0d4e47a2d39aa3cbd14ba304d30 | False | 1133 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `68`
- Chain head: `feb0fc08f06fdcef1b2440b2ce864c47d22a1ba193fd28ccb176928c46002e3a`
