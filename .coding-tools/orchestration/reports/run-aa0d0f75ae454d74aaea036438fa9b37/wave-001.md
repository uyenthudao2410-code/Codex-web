# Orchestration Wave 1

- Run: `aa0d0f75ae454d74aaea036438fa9b37`
- Wave: `2d6b32ab0e6d46ac8ae58f2f5926aa1f`
- Objective: Fix the controlled runtime activation/restart preflight so a long-lived P5 experiment ledger anchor run (runs.metadata_json.p5_experiment=true) is not misclassified as an active EOCL execution run. Preserve current_active_run semantics globally. Add a narrowly named OrchestrationLedger current_active_execution_run method that returns the newest status='active' non-P5-experiment run (optionally task-scoped if useful), fail-closed on malformed DB/JSON via existing SQLite behavior. Change only activation_preflight to use that method; do not change P5 epoch lifecycle, routing, enrollment, treatment, stale reconciliation, or public tool count. Update existing activation-preflight mocks to the new method and add regressions proving: (1) a P5-only active anchor does not block activation preflight, (2) if a genuine active run exists and a newer P5 anchor also exists, the genuine run is still detected and activation is refused. Modify only the smallest source/test surface, preferably orchestration_ledger.py, coordination.py, and test_activation_preflight.py. Run focused activation/P5 tests after patch; do not commit, push, restart runtime, or touch live ledger outside ordinary test/temp data in this wave.
- Objective revision: `1`
- Objective SHA-256: `577b34528d0df0ab28eb88ee1985b4d461e14a01dc87f8b30ccba12fcf21f720`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `12d84a32648d6b27d8b916a6aa47f718ffcff866`
- Worktree fingerprint: `4074e79276601320df0459277b82474b7b3517012e25a5cde2e5d46701cd86b8`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26912 | 2026-08-22T08:05:19.419Z | run_started |  | PREFLIGHT |  |
| 26913 | 2026-08-22T08:05:29.420Z | solution_shadow_recommended |  |  |  |
| 26914 | 2026-08-22T08:05:40.918Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26915 | 2026-08-22T08:05:41.087Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26916 | 2026-08-22T08:05:41.256Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 26917 | 2026-08-22T08:05:41.411Z | state_transition | READY | ROUTED | reason=route_selected |
| 26918 | 2026-08-22T08:05:42.189Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=255bd4ea1bdb4d53a3ee44c8c3fac323 |
| 26919 | 2026-08-22T08:05:42.358Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26920 | 2026-08-22T08:05:43.192Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=255bd4ea1bdb4d53a3ee44c8c3fac323 |
| 26921 | 2026-08-22T08:05:43.343Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26922 | 2026-08-22T08:05:44.021Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2ee733a81fdc6a73987c24e803cd16dc3b652fc66be6c12c90dad0bc7fe4d54e |
| 26923 | 2026-08-22T08:05:44.342Z | managed_process_admitted |  |  | owner=default |
| 26924 | 2026-08-22T08:05:44.619Z | managed_process_started |  |  | owner=default |
| 26925 | 2026-08-22T08:05:52.523Z | managed_process_terminal |  |  | owner=default |
| 26926 | 2026-08-22T08:05:53.461Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2ee733a81fdc6a73987c24e803cd16dc3b652fc66be6c12c90dad0bc7fe4d54e |
| 26927 | 2026-08-22T08:05:53.718Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 2ee733a81fdc6a73987c24e803cd16dc3b652fc66be6c12c90dad0bc7fe4d54e | False | 9078 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `16`
- Chain head: `bb8dc2b6c01d4cd9912cebf31d5e97fbb2f4fc3a0d08fb8ba745652f583d457d`
