# Orchestration Wave 1

- Run: `913e692f116c4d31963046197a97083c`
- Wave: `48d27d035f614b8290c952de72572e7b`
- Objective: Fix the final residual token-metrics inconsistency in Operations Overview only. Main KPI/trend/donut canonical usage_analytics remain unchanged. Secondary operational lane/model/fleet tables must not claim noncanonical delegations+lanes overlays as MEASURED token truth. Make modelBreakdown an explicit ESTIMATED/SCENARIO view from performance trace only, remove the dead legacy measuredUsage aggregator, label model/fleet token and cost columns as ESTIMATED/SCENARIO, and ensure no visible secondary token/cost number can be mistaken for canonical measured billing. Preserve lane operational state/calls and all unrelated WIP. Add focused regression. No restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `fd3cd2f12d038d7aece8f2fbe80b19e02c4d4189075037a6f41f1dcf9f8133e7`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21472 | 2026-08-19T10:03:54.594Z | run_started |  | PREFLIGHT |  |
| 21473 | 2026-08-19T10:03:55.763Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21474 | 2026-08-19T10:05:03.551Z | solution_shadow_recommended |  |  |  |
| 21475 | 2026-08-19T10:05:17.496Z | managed_process_admitted |  |  | owner=default |
| 21476 | 2026-08-19T10:05:17.709Z | managed_process_started |  |  | owner=default |
| 21477 | 2026-08-19T10:05:19.372Z | managed_process_terminal |  |  | owner=default |
| 21478 | 2026-08-19T10:05:27.281Z | managed_process_admitted |  |  | owner=default |
| 21479 | 2026-08-19T10:05:27.512Z | managed_process_started |  |  | owner=default |
| 21480 | 2026-08-19T10:05:27.942Z | managed_process_terminal |  |  | owner=default |
| 21481 | 2026-08-19T10:05:35.060Z | managed_process_admitted |  |  | owner=default |
| 21482 | 2026-08-19T10:05:35.379Z | managed_process_started |  |  | owner=default |
| 21483 | 2026-08-19T10:05:35.773Z | managed_process_terminal |  |  | owner=default |
| 21484 | 2026-08-19T10:05:44.409Z | managed_process_admitted |  |  | owner=default |
| 21485 | 2026-08-19T10:05:44.809Z | managed_process_started |  |  | owner=default |
| 21486 | 2026-08-19T10:05:45.240Z | managed_process_terminal |  |  | owner=default |
| 21487 | 2026-08-19T10:05:53.244Z | managed_process_admitted |  |  | owner=default |
| 21488 | 2026-08-19T10:05:53.459Z | managed_process_started |  |  | owner=default |
| 21489 | 2026-08-19T10:05:53.924Z | managed_process_terminal |  |  | owner=default |
| 21490 | 2026-08-19T10:06:34.999Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21491 | 2026-08-19T10:06:35.185Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21492 | 2026-08-19T10:06:35.326Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21493 | 2026-08-19T10:06:35.472Z | state_transition | READY | ROUTED | reason=route_selected |
| 21494 | 2026-08-19T10:06:36.061Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c00ddcf9d2634487ab4600e9a6f30cf7 |
| 21495 | 2026-08-19T10:06:36.248Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21496 | 2026-08-19T10:06:36.718Z | patch_surface_observed |  |  |  |
| 21497 | 2026-08-19T10:06:36.972Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c00ddcf9d2634487ab4600e9a6f30cf7 |
| 21498 | 2026-08-19T10:06:37.122Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21499 | 2026-08-19T10:06:37.472Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b62a10c92294854192fd32ff69aa29ed7313054c5a12435ed7dc1ec869ca29f0 |
| 21500 | 2026-08-19T10:06:38.009Z | managed_process_admitted |  |  | owner=default |
| 21501 | 2026-08-19T10:06:38.261Z | managed_process_started |  |  | owner=default |
| 21502 | 2026-08-19T10:06:38.728Z | managed_process_terminal |  |  | owner=default |
| 21503 | 2026-08-19T10:06:39.124Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=b62a10c92294854192fd32ff69aa29ed7313054c5a12435ed7dc1ec869ca29f0 |
| 21504 | 2026-08-19T10:06:39.298Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21505 | 2026-08-19T10:06:39.484Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21506 | 2026-08-19T10:06:39.648Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | b62a10c92294854192fd32ff69aa29ed7313054c5a12435ed7dc1ec869ca29f0 | False | 1157 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `673292e148d6a3da91956c7d87bc634b5e09b05daa577acf2a168d16b914f303`
