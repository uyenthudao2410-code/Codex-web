# Orchestration Wave 1

- Run: `03fd5fbb0cc34177972b6065150c8f73`
- Wave: `af3c06c1bc6e4ad09ab18c891c4376dc`
- Objective: Continue the accepted token-usage master-plan implementation. Implement the smallest coherent W2 correctness delta proven by prepare: controller turn usage must deduplicate across reconnect/REPLAN wave boundaries within the same RUN, instead of deriving the controller economic identity from wave_id. Preserve the first exact attribution event; retrying the same exact controller turn receipt in a later wave must return duplicate and must not double-count economics, while a conflicting receipt for the same RUN+turn identity must still fail closed as different evidence. Keep provider UsageEvent identity behavior unchanged. Do not add a database/framework, do not fabricate session/coverage data, preserve unknown_not_zero and all unrelated dirty work. No commit, push, restart, package, release or deploy.
- Objective revision: `1`
- Objective SHA-256: `f217b89c4f63f345a60f35485a6694c018bf5e39096820c719255509a940b094`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `808eed8f72b06394accf31267b8bb5211e6dca404551be197fd575a9030acbfc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33562 | 2026-08-31T18:36:16.236Z | run_started |  | PREFLIGHT |  |
| 33563 | 2026-08-31T18:36:16.790Z | observation_span_recorded |  |  |  |
| 33564 | 2026-08-31T18:36:17.003Z | solution_shadow_recommended |  |  |  |
| 33565 | 2026-08-31T18:36:17.209Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33566 | 2026-08-31T18:36:17.410Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33567 | 2026-08-31T18:36:17.618Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 33568 | 2026-08-31T18:36:17.811Z | state_transition | READY | ROUTED | reason=route_selected |
| 33569 | 2026-08-31T18:36:18.075Z | observation_span_recorded |  |  |  |
| 33570 | 2026-08-31T18:36:19.127Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1fd7eecd69554bada3c4f97e7d862328 |
| 33571 | 2026-08-31T18:36:19.329Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33572 | 2026-08-31T18:36:20.223Z | observation_span_recorded |  |  |  |
| 33573 | 2026-08-31T18:36:20.584Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1fd7eecd69554bada3c4f97e7d862328 |
| 33574 | 2026-08-31T18:36:20.810Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33575 | 2026-08-31T18:36:21.746Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=988cd90d7ffc2419c7a08bf31d56ee2224b032c6c159a06a835865b6423a4750 |
| 33576 | 2026-08-31T18:36:22.118Z | managed_process_admitted |  |  | owner=default |
| 33577 | 2026-08-31T18:36:22.544Z | managed_process_started |  |  | owner=default |
| 33578 | 2026-08-31T18:36:27.745Z | managed_process_terminal |  |  | owner=default |
| 33579 | 2026-08-31T18:36:29.343Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=988cd90d7ffc2419c7a08bf31d56ee2224b032c6c159a06a835865b6423a4750 |
| 33580 | 2026-08-31T18:36:29.747Z | observation_span_recorded |  |  |  |
| 33581 | 2026-08-31T18:36:29.986Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 33588 | 2026-08-31T18:57:24.684Z | managed_process_admitted |  |  | owner=default |
| 33589 | 2026-08-31T18:57:25.098Z | managed_process_started |  |  | owner=default |
| 33590 | 2026-08-31T18:57:25.660Z | managed_process_terminal |  |  | owner=default |
| 33591 | 2026-08-31T18:57:32.768Z | managed_process_admitted |  |  | owner=default |
| 33592 | 2026-08-31T18:57:33.260Z | managed_process_started |  |  | owner=default |
| 33593 | 2026-08-31T18:57:33.781Z | managed_process_terminal |  |  | owner=default |
| 33594 | 2026-08-31T18:57:39.947Z | managed_process_admitted |  |  | owner=default |
| 33595 | 2026-08-31T18:57:40.285Z | managed_process_started |  |  | owner=default |
| 33596 | 2026-08-31T18:57:40.735Z | managed_process_terminal |  |  | owner=default |
| 33597 | 2026-08-31T18:57:48.594Z | managed_process_admitted |  |  | owner=default |
| 33598 | 2026-08-31T18:57:49.040Z | managed_process_started |  |  | owner=default |
| 33599 | 2026-08-31T18:57:49.535Z | managed_process_terminal |  |  | owner=default |
| 33600 | 2026-08-31T18:57:59.464Z | managed_process_admitted |  |  | owner=default |
| 33601 | 2026-08-31T18:57:59.823Z | managed_process_started |  |  | owner=default |
| 33602 | 2026-08-31T18:58:00.391Z | managed_process_terminal |  |  | owner=default |
| 33603 | 2026-08-31T18:58:14.619Z | failure_observed | ACCEPTING | ACCEPTING | reason=W2 acceptance rejected: exact current source still derives build_usage_event usage_id from run_id + wave_id + identity_key, while controller identity_key=turn_id. Therefore the same exact ChatWeb controller turn retried after REPLAN/new wave within the same RUN receives a different usage_id and can double-count economics. The passing proof did not exercise this cross-wave invariant, and the wave has no durable file receipts on the causal W2 files. REPLAN same RUN with a controller-specific wave-independent economic identity plus discriminating cross-wave duplicate/conflict tests; preserve provider UsageEvent identity behavior.; failure_class=SOL_REJECTED |
| 33604 | 2026-08-31T18:58:14.849Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 33605 | 2026-08-31T18:58:15.211Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 988cd90d7ffc2419c7a08bf31d56ee2224b032c6c159a06a835865b6423a4750 | False | 7186 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `68eebbb3d4ed53474a066a82e2b7ed4159dd304a63399378475eb04de5050a26`
