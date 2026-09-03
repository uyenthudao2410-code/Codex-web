# Orchestration Wave 1

- Run: `e5ec63f077a148a08c26094ca472dcfd`
- Wave: `b94150518db141d5b8900d150a84a19f`
- Objective: Fix the explicit task_control supervisor restart deadlock under an invalid READY adoption guard. RecoveryHost.superviseOnce must allow only the one-shot supervisor restart ticket consumer to run when readyAdoptionBlocked is true while the durable activation epoch is still READY; normal watchdog auto-recovery and all other runtime mutation must remain blocked. Any non-READY durable activation epoch must continue to block restart-ticket consumption. Preserve accepted source-checkpoint validation, activation fences, connector proof validation, and current direct runtime.restart/code.activate_update behavior. Add a focused regression proving the ticket consumer runs in the READY-adoption-blocked case without invoking ordinary orchestrator.supervise, and remains blocked once a non-READY replacement epoch is current.
- Objective revision: `1`
- Objective SHA-256: `a70fceb3f1337145c8f4862dbd0389f924e63945f15dbee02a627a8990ec718a`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `30ff062c936c0a2b4e5f5262b62c71320d534225651e826822a3bac178059cb3`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37272 | 2026-09-03T10:13:25.611Z | run_started |  | PREFLIGHT |  |
| 37273 | 2026-09-03T10:13:26.030Z | observation_span_recorded |  |  |  |
| 37274 | 2026-09-03T10:13:28.049Z | observation_span_recorded |  |  |  |
| 37275 | 2026-09-03T10:13:28.290Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37276 | 2026-09-03T10:14:11.366Z | solution_shadow_recommended |  |  |  |
| 37277 | 2026-09-03T10:14:11.643Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37278 | 2026-09-03T10:14:11.877Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37279 | 2026-09-03T10:14:12.110Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 37280 | 2026-09-03T10:14:12.343Z | state_transition | READY | ROUTED | reason=route_selected |
| 37281 | 2026-09-03T10:14:12.584Z | observation_span_recorded |  |  |  |
| 37282 | 2026-09-03T10:14:14.250Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cb38b83180734d718d2ffd79a00bea65 |
| 37283 | 2026-09-03T10:14:14.476Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37284 | 2026-09-03T10:14:16.002Z | patch_surface_observed |  |  |  |
| 37285 | 2026-09-03T10:14:16.304Z | observation_span_recorded |  |  |  |
| 37286 | 2026-09-03T10:14:16.788Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cb38b83180734d718d2ffd79a00bea65 |
| 37287 | 2026-09-03T10:14:17.035Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37288 | 2026-09-03T10:14:18.482Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ab52342f78f08db5f2c8d09ded9d61797153967b2d8831c2d8cd5550a4414dac |
| 37289 | 2026-09-03T10:14:18.938Z | managed_process_admitted |  |  | owner=default |
| 37290 | 2026-09-03T10:14:19.243Z | managed_process_started |  |  | owner=default |
| 37291 | 2026-09-03T10:14:29.944Z | managed_process_terminal |  |  | owner=default |
| 37292 | 2026-09-03T10:14:30.868Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ab52342f78f08db5f2c8d09ded9d61797153967b2d8831c2d8cd5550a4414dac |
| 37293 | 2026-09-03T10:14:32.117Z | observation_span_recorded |  |  |  |
| 37294 | 2026-09-03T10:14:32.318Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37295 | 2026-09-03T10:15:48.169Z | managed_process_admitted |  |  | owner=chatweb-restart-deadlock-accept-hash |
| 37296 | 2026-09-03T10:15:48.442Z | managed_process_started |  |  | owner=chatweb-restart-deadlock-accept-hash |
| 37297 | 2026-09-03T10:15:49.133Z | managed_process_terminal |  |  | owner=chatweb-restart-deadlock-accept-hash |
| 37298 | 2026-09-03T10:16:04.998Z | quality_outcome_recorded |  |  |  |
| 37299 | 2026-09-03T10:16:05.368Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 37300 | 2026-09-03T10:16:05.826Z | observation_span_recorded |  |  |  |
| 37301 | 2026-09-03T10:16:06.257Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ab52342f78f08db5f2c8d09ded9d61797153967b2d8831c2d8cd5550a4414dac | False | 12014 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ad096eff05c74a2c9dbdbf2b810b2270 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | dd767a343baa357c8394b034e8dd02640625864e6d8bcddaa007a031ee7639bc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `b46d3bcb43f39f68b8c8ccadd1e9089283a4365ccc21a5586af2a482287dea26`
