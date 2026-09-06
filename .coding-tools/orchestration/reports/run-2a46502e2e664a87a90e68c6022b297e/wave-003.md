# Orchestration Wave 3

- Run: `2a46502e2e664a87a90e68c6022b297e`
- Wave: `5f6825a55cf149ab833a8405e4c98f4d`
- Objective: DASHBOARD-MEASUREMENT-01: correct the current dashboard measurement projection and UI so missing or invalid by_model evidence never becomes observed measured zero. Preserve known input/output when only cached tokens are unknown, distinguish unavailable versus partial breakdown from complete genuine zero, clear stale/in-flight donut totals when breakdown becomes unavailable, and add behavioral VM coverage through the actual projector/render consumer. Write only renderer/dashboard.js and tests/dashboard-measurement-behavior.test.js; preserve all unrelated WIP.
- Objective revision: `1`
- Objective SHA-256: `a46bc26fd6e4e7241617cec519dd344e8143bc3b7593030ab5bb729b63534d45`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `9a96c6355a3a95fdbcb63d9481ece44632f9d6ec4edc9dea6dc2b1968af3766d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40463 | 2026-09-05T09:35:47.624Z | wave_replanned |  | PREFLIGHT | reason=Official v2 proof isolated a single static source-oracle failure in tests/dashboard-analytics.test.js requiring the legacy measured?.byModel?.length ternary. V3 removes only that gratuitous expression-shape change while retaining the new complete/partial/unavailable status propagation, coverage guard, and behavioral VM oracles; the unchanged VM test is carried forward by exact-byte adoption. |
| 40464 | 2026-09-05T09:35:47.796Z | observation_span_recorded |  |  |  |
| 40465 | 2026-09-05T09:35:48.020Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40466 | 2026-09-05T09:35:48.200Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40467 | 2026-09-05T09:35:48.412Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40468 | 2026-09-05T09:35:48.595Z | state_transition | READY | ROUTED | reason=route_selected |
| 40469 | 2026-09-05T09:35:48.869Z | observation_span_recorded |  |  |  |
| 40470 | 2026-09-05T09:35:49.495Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=63dd7a46851645a79b3709fd24b6b9ec |
| 40471 | 2026-09-05T09:35:49.645Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40472 | 2026-09-05T09:35:50.144Z | existing_file_adoption_observed |  |  |  |
| 40473 | 2026-09-05T09:35:50.331Z | patch_surface_observed |  |  |  |
| 40474 | 2026-09-05T09:35:50.480Z | observation_span_recorded |  |  |  |
| 40475 | 2026-09-05T09:35:50.708Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=63dd7a46851645a79b3709fd24b6b9ec |
| 40476 | 2026-09-05T09:35:50.867Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40477 | 2026-09-05T09:35:51.415Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=badbe2cd562493a05edaa50a3171e019795b1b8444b1265a480f2f6cd2d06ca1 |
| 40478 | 2026-09-05T09:35:51.799Z | managed_process_admitted |  |  | owner=default |
| 40479 | 2026-09-05T09:35:52.102Z | managed_process_started |  |  | owner=default |
| 40480 | 2026-09-05T09:35:52.586Z | managed_process_terminal |  |  | owner=default |
| 40481 | 2026-09-05T09:35:58.243Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=badbe2cd562493a05edaa50a3171e019795b1b8444b1265a480f2f6cd2d06ca1 |
| 40482 | 2026-09-05T09:35:59.059Z | observation_span_recorded |  |  |  |
| 40483 | 2026-09-05T09:35:59.304Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 40484 | 2026-09-05T09:40:12.128Z | quality_outcome_recorded |  |  |  |
| 40485 | 2026-09-05T09:40:12.304Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 40486 | 2026-09-05T09:40:12.630Z | observation_span_recorded |  |  |  |
| 40487 | 2026-09-05T09:40:12.840Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | badbe2cd562493a05edaa50a3171e019795b1b8444b1265a480f2f6cd2d06ca1 | False | 6375 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ae0c65c6b44f463e83e73fb3265f248d | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 243893d52d8f8f6d5c5ef6349a197f911195db3a5c695d311a5fffa5f43635d3 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `72`
- Chain head: `f5afc8ad4e17aa4076ec736d39ced0253b773f3b35a8cc00fd4a2eddf3929989`
