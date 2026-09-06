# Orchestration Wave 2

- Run: `2a46502e2e664a87a90e68c6022b297e`
- Wave: `d8b257470bd6410693b5c5061509e374`
- Objective: DASHBOARD-MEASUREMENT-01: correct the current dashboard measurement projection and UI so missing or invalid by_model evidence never becomes observed measured zero. Preserve known input/output when only cached tokens are unknown, distinguish unavailable versus partial breakdown from complete genuine zero, clear stale/in-flight donut totals when breakdown becomes unavailable, and add behavioral VM coverage through the actual projector/render consumer. Write only renderer/dashboard.js and tests/dashboard-measurement-behavior.test.js; preserve all unrelated WIP.
- Objective revision: `1`
- Objective SHA-256: `a46bc26fd6e4e7241617cec519dd344e8143bc3b7593030ab5bb729b63534d45`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `dc862e5c6dcfae264d40cf621f9e25007a7e82751160249d68df79a94f14f257`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40439 | 2026-09-05T09:29:42.032Z | wave_replanned |  | PREFLIGHT | reason=Changed evidence after failed wave: retained TAP output expired, independent source review identified VM harness style.setProperty omission, exact unavailable-text mismatch, and a real by_model coverage completeness defect. Prepare only the two owned current files so v2 can patch the current bytes rather than replay v1 unchanged. |
| 40440 | 2026-09-05T09:29:42.253Z | observation_span_recorded |  |  |  |
| 40441 | 2026-09-05T09:29:55.085Z | observation_span_recorded |  |  |  |
| 40442 | 2026-09-05T09:29:55.315Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 40443 | 2026-09-05T09:32:34.772Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40444 | 2026-09-05T09:32:34.934Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40445 | 2026-09-05T09:32:35.106Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40446 | 2026-09-05T09:32:35.289Z | state_transition | READY | ROUTED | reason=route_selected |
| 40447 | 2026-09-05T09:32:35.546Z | observation_span_recorded |  |  |  |
| 40448 | 2026-09-05T09:32:36.187Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=85611ef74d6143499aafeed8243efbc3 |
| 40449 | 2026-09-05T09:32:36.396Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40450 | 2026-09-05T09:32:36.921Z | patch_surface_observed |  |  |  |
| 40451 | 2026-09-05T09:32:37.119Z | observation_span_recorded |  |  |  |
| 40452 | 2026-09-05T09:32:37.445Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=85611ef74d6143499aafeed8243efbc3 |
| 40453 | 2026-09-05T09:32:37.618Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40454 | 2026-09-05T09:32:38.068Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=bf043bf07ca940b79944d95fa26b9abc63397dfdbddfe3ff27690ed35fa814e5 |
| 40455 | 2026-09-05T09:32:38.491Z | managed_process_admitted |  |  | owner=default |
| 40456 | 2026-09-05T09:32:38.806Z | managed_process_started |  |  | owner=default |
| 40457 | 2026-09-05T09:32:39.284Z | managed_process_terminal |  |  | owner=default |
| 40458 | 2026-09-05T09:32:39.618Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=bf043bf07ca940b79944d95fa26b9abc63397dfdbddfe3ff27690ed35fa814e5 |
| 40459 | 2026-09-05T09:32:39.814Z | observation_span_recorded |  |  |  |
| 40460 | 2026-09-05T09:32:40.001Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 40461 | 2026-09-05T09:32:40.160Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 40462 | 2026-09-05T09:32:40.374Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | bf043bf07ca940b79944d95fa26b9abc63397dfdbddfe3ff27690ed35fa814e5 | False | 1250 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `72`
- Chain head: `f5afc8ad4e17aa4076ec736d39ced0253b773f3b35a8cc00fd4a2eddf3929989`
