# Orchestration Wave 1

- Run: `0ca7f60e56544df9aadb9fb89f7df48f`
- Wave: `e3f93399444a47ed9fec9042b83bfce6`
- Objective: Strengthen the stateless exact-run continuation regression so it proves a run whose controller has been explicitly transferred to another active principal is not auto-recovered into the old ChatWeb application context. This is a test-only hardening change; do not change production behavior.
- Objective revision: `1`
- Objective SHA-256: `e011cc9a8491a95437534a09a6f1532dc926bf70e2fecc5f265d483ac0a6d432`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `0557afa6c3aa3e02c2664d312b860973f28d3fc5`
- Worktree fingerprint: `282c65bf4297ce18b1ac250839b6970df403f16c6a7c9430953177976272cdf4`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 29706 | 2026-08-25T15:02:43.024Z | run_started |  | PREFLIGHT |  |
| 29707 | 2026-08-25T15:02:43.369Z | observation_span_recorded |  |  |  |
| 29708 | 2026-08-25T15:02:43.520Z | solution_shadow_recommended |  |  |  |
| 29709 | 2026-08-25T15:02:44.251Z | observation_span_recorded |  |  |  |
| 29710 | 2026-08-25T15:02:44.406Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 29711 | 2026-08-25T15:02:44.543Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 29712 | 2026-08-25T15:02:44.676Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 29713 | 2026-08-25T15:02:44.796Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 29714 | 2026-08-25T15:02:44.928Z | state_transition | READY | ROUTED | reason=route_selected |
| 29715 | 2026-08-25T15:02:45.064Z | observation_span_recorded |  |  |  |
| 29716 | 2026-08-25T15:02:45.859Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b1290b295ccf4148911b6f545b2d674c |
| 29717 | 2026-08-25T15:02:45.983Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 29718 | 2026-08-25T15:02:46.753Z | patch_surface_observed |  |  |  |
| 29719 | 2026-08-25T15:02:46.909Z | observation_span_recorded |  |  |  |
| 29720 | 2026-08-25T15:02:47.141Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b1290b295ccf4148911b6f545b2d674c |
| 29721 | 2026-08-25T15:02:47.251Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 29722 | 2026-08-25T15:02:47.938Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=eb12462a3ed941d4c3ce162e59df4405ad7f6002fe29e9c04dc6e2bb60f78627 |
| 29723 | 2026-08-25T15:02:48.301Z | managed_process_admitted |  |  | owner=default |
| 29724 | 2026-08-25T15:02:48.543Z | managed_process_started |  |  | owner=default |
| 29725 | 2026-08-25T15:03:03.759Z | managed_process_terminal |  |  | owner=default |
| 29726 | 2026-08-25T15:03:10.442Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=eb12462a3ed941d4c3ce162e59df4405ad7f6002fe29e9c04dc6e2bb60f78627 |
| 29727 | 2026-08-25T15:03:11.328Z | observation_span_recorded |  |  |  |
| 29728 | 2026-08-25T15:03:11.476Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | eb12462a3ed941d4c3ce162e59df4405ad7f6002fe29e9c04dc6e2bb60f78627 | False | 22171 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `2ab77d4c7fda9564e1cfbe607269f385fc80f2bea10b021e3f8c6f0edaefff39`
