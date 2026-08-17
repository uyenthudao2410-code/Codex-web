# Orchestration Wave 1

- Run: `2d5264fdc2dc4f0fb20516008be2be98`
- Wave: `0c17f716a2374c80809fc49ee6dc6397`
- Objective: P1.2 closure only. Verify that the accepted P1.2 implementation defines a durable causal eligible-run denominator for organic Electron host correlation, excludes legacy/history without the marker instead of inferring eligibility, preserves controlled runs that only carry trace_id/turn_id as ineligible, and reports host_spans_total/host_spans_with_run_binding/host_binding_rate/eligible_runs_total/eligible_runs_with_host_span/eligible_run_host_coverage without timestamp proximity. Determine the exact smallest remaining closure work and fresh verification commands. Do not mutate, do not implement P1.3, do not restart/activate runtime, do not change routing/public schema/DB/release artifacts.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `e0abb52ea3b4e0acacb35dc83e86116ab0d85b3161f52df6b3eafa0184b1258e`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14442 | 2026-08-17T16:10:28.065Z | run_started |  | PREFLIGHT |  |
| 14443 | 2026-08-17T16:10:33.040Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14444 | 2026-08-17T16:12:17.195Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14445 | 2026-08-17T16:12:17.317Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14446 | 2026-08-17T16:12:17.433Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 14447 | 2026-08-17T16:12:17.575Z | state_transition | READY | ROUTED | reason=route_selected |
| 14448 | 2026-08-17T16:12:18.166Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2d83ac1150ca41909495a8d2ce34a160 |
| 14449 | 2026-08-17T16:12:18.273Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14450 | 2026-08-17T16:12:18.998Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2d83ac1150ca41909495a8d2ce34a160 |
| 14451 | 2026-08-17T16:12:19.154Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14452 | 2026-08-17T16:12:19.675Z | proof_cache_miss |  |  | reason=cold; stage_id=check:80a1a46bd01d26a3; input_fingerprint=837081055f8f68a93198aeeee307448539ab056e33ef8cb07d0d070374c14f88 |
| 14453 | 2026-08-17T16:12:19.898Z | managed_process_admitted |  |  | owner=default |
| 14454 | 2026-08-17T16:12:20.123Z | managed_process_started |  |  | owner=default |
| 14455 | 2026-08-17T16:12:20.642Z | managed_process_terminal |  |  | owner=default |
| 14456 | 2026-08-17T16:12:20.869Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=837081055f8f68a93198aeeee307448539ab056e33ef8cb07d0d070374c14f88 |
| 14457 | 2026-08-17T16:12:21.014Z | proof_cache_miss |  |  | reason=cold; stage_id=check:29a31c2bd9129fd5; input_fingerprint=18c1c17f0613cfa6b56e0715ca09d3f740a21e321456b655cd498e1aaa26fbc9 |
| 14458 | 2026-08-17T16:12:21.239Z | managed_process_admitted |  |  | owner=default |
| 14459 | 2026-08-17T16:12:21.482Z | managed_process_started |  |  | owner=default |
| 14460 | 2026-08-17T16:12:32.482Z | managed_process_terminal |  |  | owner=default |
| 14461 | 2026-08-17T16:12:32.701Z | proof_recorded |  |  | stage_id=check:29a31c2bd9129fd5; status=passed; cache_hit=False; input_fingerprint=18c1c17f0613cfa6b56e0715ca09d3f740a21e321456b655cd498e1aaa26fbc9 |
| 14462 | 2026-08-17T16:12:32.839Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b38e9e9be738c35e; input_fingerprint=2dd01c7b37e79246c989e06d2942d03dd89e72822bb020c65aab05d3d8b478c9 |
| 14463 | 2026-08-17T16:12:33.095Z | managed_process_admitted |  |  | owner=default |
| 14464 | 2026-08-17T16:12:33.328Z | managed_process_started |  |  | owner=default |
| 14465 | 2026-08-17T16:12:33.678Z | managed_process_terminal |  |  | owner=default |
| 14466 | 2026-08-17T16:12:33.925Z | proof_recorded |  |  | stage_id=check:b38e9e9be738c35e; status=passed; cache_hit=False; input_fingerprint=2dd01c7b37e79246c989e06d2942d03dd89e72822bb020c65aab05d3d8b478c9 |
| 14467 | 2026-08-17T16:12:34.065Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=4d157e8ef2244c2d5ebc207310bc84e214f81f57c854f5637fcb206a371ad527 |
| 14468 | 2026-08-17T16:12:34.304Z | managed_process_admitted |  |  | owner=default |
| 14469 | 2026-08-17T16:12:34.548Z | managed_process_started |  |  | owner=default |
| 14470 | 2026-08-17T16:12:35.884Z | managed_process_terminal |  |  | owner=default |
| 14471 | 2026-08-17T16:12:42.316Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=4d157e8ef2244c2d5ebc207310bc84e214f81f57c854f5637fcb206a371ad527 |
| 14472 | 2026-08-17T16:12:42.459Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14473 | 2026-08-17T16:14:14.600Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14474 | 2026-08-17T16:14:14.963Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80a1a46bd01d26a3 | passed | 837081055f8f68a93198aeeee307448539ab056e33ef8cb07d0d070374c14f88 | False | 982 | 0 |
| check:29a31c2bd9129fd5 | passed | 18c1c17f0613cfa6b56e0715ca09d3f740a21e321456b655cd498e1aaa26fbc9 | False | 11508 | 0 |
| check:b38e9e9be738c35e | passed | 2dd01c7b37e79246c989e06d2942d03dd89e72822bb020c65aab05d3d8b478c9 | False | 846 | 0 |
| verify:tests | passed | 4d157e8ef2244c2d5ebc207310bc84e214f81f57c854f5637fcb206a371ad527 | False | 7954 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 224bbee3695d45c893f91a8e9ff99696 | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 811f0ddf94007726841647c73d67dec4e6a310b5be311a378fa3bff8ddec624b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `ee038fdfe54c921148c576193adb56dfe35813e6aeb110ae14dfa6c18881bf8e`
