# Orchestration Wave 1

- Run: `f7f34289300d42dda4a8d556a8183459`
- Wave: `43cf4f035d2542e0ae12f0c966ed9237`
- Objective: Implement the user-authorized bounded exact-stale maintenance seam in Recovery Host full-clean replacement. Parse only a strict reserved reason prefix exact_stale_runs:<comma-separated 32-lowerhex-run-ids>, max 16 unique IDs. In continueReplacement, while the old canonical Coding MCP is already stopped and before orchestrator.start, sequentially run the existing reconcile_exact_stale_run.py through pythonStatus/execFile without shell: fresh preflight per ID, validate physical+logical HEX64 snapshot hashes, then reconcile with --runtime-stopped and exact expected hashes; require schema_version=1, reconciliation.chain_ok=true, and postflight target stale/RECONCILED_STALE/already_reconciled=true. Any malformed request, Python/script failure, receipt mismatch, or deadline expiry must fail the activation closed before MCP start. Ordinary restart reasons remain unchanged/no-op. Add focused tests proving sequential maintenance occurs before MCP start and malformed reserved reasons prevent start. Do not change public MCP tool schema/count, Python ledger logic, unrelated source, Git history, or external services.
- Objective revision: `1`
- Objective SHA-256: `bb863ff4cd2390b87937cb5c9bfa35cc3dd3cca0d821a04c8e4bfa934986cb9c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `d930a6901c3810b35d954108bef4714bf1d28faf541b797c09d5defe6aed8193`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42974 | 2026-09-07T02:55:36.610Z | run_started |  | PREFLIGHT |  |
| 42975 | 2026-09-07T02:55:37.134Z | observation_span_recorded |  |  |  |
| 42976 | 2026-09-07T02:55:37.343Z | solution_shadow_recommended |  |  |  |
| 42977 | 2026-09-07T02:55:37.881Z | observation_span_recorded |  |  |  |
| 42978 | 2026-09-07T02:55:38.134Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42979 | 2026-09-07T02:55:38.369Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42980 | 2026-09-07T02:55:38.562Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42981 | 2026-09-07T02:55:38.820Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 42982 | 2026-09-07T02:55:39.003Z | state_transition | READY | ROUTED | reason=route_selected |
| 42983 | 2026-09-07T02:55:39.213Z | observation_span_recorded |  |  |  |
| 42984 | 2026-09-07T02:55:39.719Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=79dacea023dc48edb0546f86fc446529 |
| 42985 | 2026-09-07T02:55:39.920Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42986 | 2026-09-07T02:55:40.391Z | patch_surface_observed |  |  |  |
| 42987 | 2026-09-07T02:55:40.651Z | patch_surface_observed |  |  |  |
| 42988 | 2026-09-07T02:55:40.903Z | patch_surface_observed |  |  |  |
| 42989 | 2026-09-07T02:55:41.203Z | patch_surface_observed |  |  |  |
| 42990 | 2026-09-07T02:55:41.402Z | observation_span_recorded |  |  |  |
| 42991 | 2026-09-07T02:55:41.776Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=79dacea023dc48edb0546f86fc446529 |
| 42992 | 2026-09-07T02:55:41.956Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42993 | 2026-09-07T02:55:42.340Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fdd8d9bbdabfc13b; input_fingerprint=a4ebc0ca72cf44f060152c278948a65627fa50ff125d0244a529fc4111dadeaa |
| 42994 | 2026-09-07T02:55:42.709Z | managed_process_admitted |  |  | owner=default |
| 42995 | 2026-09-07T02:55:43.044Z | managed_process_started |  |  | owner=default |
| 42996 | 2026-09-07T02:55:43.478Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 42997 | 2026-09-07T02:55:43.883Z | proof_recorded |  |  | stage_id=check:fdd8d9bbdabfc13b; status=passed; cache_hit=False; input_fingerprint=a4ebc0ca72cf44f060152c278948a65627fa50ff125d0244a529fc4111dadeaa |
| 42998 | 2026-09-07T02:55:44.135Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=bb8173e0f0aec4083f634ce96a31250ec5e67f1db6d9420f056e2e3fd93cb097 |
| 42999 | 2026-09-07T02:55:44.590Z | managed_process_admitted |  |  | owner=default |
| 43000 | 2026-09-07T02:55:44.935Z | managed_process_started |  |  | owner=default |
| 43001 | 2026-09-07T02:55:46.962Z | managed_process_terminal |  |  | owner=default |
| 43002 | 2026-09-07T02:55:54.047Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=bb8173e0f0aec4083f634ce96a31250ec5e67f1db6d9420f056e2e3fd93cb097 |
| 43003 | 2026-09-07T02:55:54.592Z | observation_span_recorded |  |  |  |
| 43004 | 2026-09-07T02:55:54.803Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43005 | 2026-09-07T02:59:53.913Z | observation_span_recorded |  |  |  |
| 43006 | 2026-09-07T02:59:54.111Z | failure_observed | ACCEPTING | ACCEPTING | reason=Focused suite is 47/49: both new exact-stale tests fail before the maintenance seam because their test clock/deadline is already expired. Production patch is not accepted; replan only the test fixture clock/deadline.; failure_class=SOL_REJECTED |
| 43007 | 2026-09-07T02:59:54.314Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 43008 | 2026-09-07T02:59:54.518Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fdd8d9bbdabfc13b | passed | a4ebc0ca72cf44f060152c278948a65627fa50ff125d0244a529fc4111dadeaa | False | 941 | 0 |
| verify:tests | passed | bb8173e0f0aec4083f634ce96a31250ec5e67f1db6d9420f056e2e3fd93cb097 | False | 9438 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `100`
- Chain head: `d131d7d6fc7b04b21d22ab14c6e56caacc5eaa3ccda8de8ab8f99f6586968fad`
