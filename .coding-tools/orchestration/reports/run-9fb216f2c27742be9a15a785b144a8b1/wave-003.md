# Orchestration Wave 3

- Run: `9fb216f2c27742be9a15a785b144a8b1`
- Wave: `f8330e79a9b0490daa4b97bf870bf99e`
- Objective: Finalize token dashboard hierarchy without changing token accounting: rename the canonical provider UsageEvent tile from the ambiguous TỔNG TOKEN label to TOKEN PROVIDER, preserve TOKEN CHATWEB as the primary per-turn/session structural measurement, and strengthen the regression test so renderChatTurnCard cannot depend on provider measured data or provider tile IDs. Preserve the existing local ChatWeb hero-card styling exactly.
- Objective revision: `1`
- Objective SHA-256: `02036fc0223dd1e6e2131beb2a96fca38b96196547ac8dde69a884308f0851df`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `49ed1ecd58b423442ece115a9b5c291c7328227681505455f8b61de6673bbede`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39592 | 2026-09-04T11:19:31.315Z | wave_replanned |  | PREFLIGHT | reason=Focused proof showed exactly one failure: an existing regression test expects the hidden ACCEPTED marker removed from the provider tile comment. The prior retry was blocked by the operator-report ACK gate before patch preflight. With that report now acknowledged, this wave restores only the hidden ACCEPTED RESULT marker while preserving the visible TOKEN PROVIDER label and the new isolation invariant. |
| 39593 | 2026-09-04T11:19:31.514Z | observation_span_recorded |  |  |  |
| 39594 | 2026-09-04T11:19:31.716Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39595 | 2026-09-04T11:19:31.896Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39596 | 2026-09-04T11:19:32.048Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 39597 | 2026-09-04T11:19:32.226Z | state_transition | READY | ROUTED | reason=route_selected |
| 39598 | 2026-09-04T11:19:32.397Z | observation_span_recorded |  |  |  |
| 39599 | 2026-09-04T11:19:32.932Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=65ac54ac4c534f78997684fe040f19ad |
| 39600 | 2026-09-04T11:19:33.105Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39601 | 2026-09-04T11:19:33.511Z | patch_surface_observed |  |  |  |
| 39602 | 2026-09-04T11:19:33.713Z | observation_span_recorded |  |  |  |
| 39603 | 2026-09-04T11:19:33.963Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=65ac54ac4c534f78997684fe040f19ad |
| 39604 | 2026-09-04T11:19:34.136Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39605 | 2026-09-04T11:19:34.573Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a5fd467c211c16c7; input_fingerprint=4d9661ae7b592e3f78d57499316bbbb1dd20779d4f8d0e17fe62fb3af225cf00 |
| 39606 | 2026-09-04T11:19:34.954Z | managed_process_admitted |  |  | owner=default |
| 39607 | 2026-09-04T11:19:35.225Z | managed_process_started |  |  | owner=default |
| 39608 | 2026-09-04T11:19:35.651Z | managed_process_terminal |  |  | owner=default |
| 39609 | 2026-09-04T11:19:35.968Z | proof_recorded |  |  | stage_id=check:a5fd467c211c16c7; status=passed; cache_hit=False; input_fingerprint=4d9661ae7b592e3f78d57499316bbbb1dd20779d4f8d0e17fe62fb3af225cf00 |
| 39610 | 2026-09-04T11:19:36.156Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2e8bfe8d14fd95de01212fdf24d7d2b2b6121026994df7629db0af82a0c30cec |
| 39611 | 2026-09-04T11:19:36.461Z | managed_process_admitted |  |  | owner=default |
| 39612 | 2026-09-04T11:19:36.759Z | managed_process_started |  |  | owner=default |
| 39613 | 2026-09-04T11:19:37.179Z | managed_process_terminal |  |  | owner=default |
| 39614 | 2026-09-04T11:19:41.105Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2e8bfe8d14fd95de01212fdf24d7d2b2b6121026994df7629db0af82a0c30cec |
| 39615 | 2026-09-04T11:19:41.673Z | observation_span_recorded |  |  |  |
| 39616 | 2026-09-04T11:19:41.859Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 39617 | 2026-09-04T11:20:39.134Z | managed_process_admitted |  |  | owner=default |
| 39618 | 2026-09-04T11:20:39.420Z | managed_process_started |  |  | owner=default |
| 39619 | 2026-09-04T11:20:39.876Z | managed_process_terminal |  |  | owner=default |
| 39620 | 2026-09-04T11:21:03.129Z | observation_span_recorded |  |  |  |
| 39621 | 2026-09-04T11:21:03.343Z | failure_observed | ACCEPTING | ACCEPTING | reason=Acceptance provenance gap only: two pre-existing dirty acceptance paths were not durably adopted inside the final wave. Code and proof are green. Replan to an exact-byte no-write adoption wave for the current dashboard slice, then rerun the same proof and accept on that exact fingerprint.; failure_class=SOL_REJECTED |
| 39622 | 2026-09-04T11:21:03.534Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 39623 | 2026-09-04T11:21:03.758Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a5fd467c211c16c7 | passed | 4d9661ae7b592e3f78d57499316bbbb1dd20779d4f8d0e17fe62fb3af225cf00 | False | 1093 | 0 |
| verify:tests | passed | 2e8bfe8d14fd95de01212fdf24d7d2b2b6121026994df7629db0af82a0c30cec | False | 4609 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `cbf6c2dfc1b6de0191bf136d8dd5f29df9d039e6bdeb25ceb3781f197810bfdb`
