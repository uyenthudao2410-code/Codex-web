# Orchestration Wave 2

- Run: `913e692f116c4d31963046197a97083c`
- Wave: `85e2caa364e04235a20819ac18500a2b`
- Objective: Fix the final residual token-metrics inconsistency in Operations Overview only. Main KPI/trend/donut canonical usage_analytics remain unchanged. Secondary operational lane/model/fleet tables must not claim noncanonical delegations+lanes overlays as MEASURED token truth. Make modelBreakdown an explicit ESTIMATED/SCENARIO view from performance trace only, remove the dead legacy measuredUsage aggregator, label model/fleet token and cost columns as ESTIMATED/SCENARIO, and ensure no visible secondary token/cost number can be mistaken for canonical measured billing. Preserve lane operational state/calls and all unrelated WIP. Add focused regression. No restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `850250883d8c0e0baccb2992abe2636c02731d50f3ceab602073f7ad5cb3c993`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21507 | 2026-08-19T10:07:20.076Z | wave_replanned |  | PREFLIGHT | reason=Fresh proof showed 20/22 dashboard tests passing. The only two failures assert the legacy measuredByLane secondary-economics behavior intentionally removed by this wave. Update those stale assertions to preserve lane-state/controller-authority checks while asserting canonical usage_analytics owns measured economics and secondary modelBreakdown stays ESTIMATED/SCENARIO. |
| 21508 | 2026-08-19T10:07:21.026Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21509 | 2026-08-19T10:07:53.117Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21510 | 2026-08-19T10:07:53.306Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21511 | 2026-08-19T10:07:53.459Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21512 | 2026-08-19T10:07:53.683Z | state_transition | READY | ROUTED | reason=route_selected |
| 21513 | 2026-08-19T10:07:54.220Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=daee171bff4944a2b69aca2c923213ed |
| 21514 | 2026-08-19T10:07:54.371Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21515 | 2026-08-19T10:07:54.830Z | patch_surface_observed |  |  |  |
| 21516 | 2026-08-19T10:07:55.120Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=daee171bff4944a2b69aca2c923213ed |
| 21517 | 2026-08-19T10:07:55.276Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21518 | 2026-08-19T10:07:55.710Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e199660166b9f0f428d4fabef297f6e07d9543f53b486238a371d1f2a8b4940d |
| 21519 | 2026-08-19T10:07:56.039Z | managed_process_admitted |  |  | owner=default |
| 21520 | 2026-08-19T10:07:56.277Z | managed_process_started |  |  | owner=default |
| 21521 | 2026-08-19T10:07:57.289Z | managed_process_terminal |  |  | owner=default |
| 21522 | 2026-08-19T10:07:57.574Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=e199660166b9f0f428d4fabef297f6e07d9543f53b486238a371d1f2a8b4940d |
| 21523 | 2026-08-19T10:07:58.039Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21524 | 2026-08-19T10:08:13.776Z | quality_outcome_recorded |  |  |  |
| 21525 | 2026-08-19T10:08:13.925Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21526 | 2026-08-19T10:08:14.226Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | e199660166b9f0f428d4fabef297f6e07d9543f53b486238a371d1f2a8b4940d | False | 1547 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0e8fce13183c4cd78f62bd13bdc16ccd | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | d2fac63c441dd4bdee47b889035964a58f1350318e16a1c3398d3a3816069282 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `673292e148d6a3da91956c7d87bc634b5e09b05daa577acf2a168d16b914f303`
