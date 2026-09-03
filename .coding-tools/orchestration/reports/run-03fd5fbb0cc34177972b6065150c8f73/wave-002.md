# Orchestration Wave 2

- Run: `03fd5fbb0cc34177972b6065150c8f73`
- Wave: `14ecacaeb4784d2492fae7a9a5dbf363`
- Objective: Continue W2 in the existing RUN after SOL_REJECTED acceptance. Implement the smallest causal cross-wave controller-usage idempotency fix. The economic identity of an exact ChatWeb controller receipt must be stable for the same RUN + turn_id across reconnect/REPLAN wave boundaries; wave_id/delegation_id remain attribution metadata and the first exact attribution event must be preserved. Replaying the same exact controller receipt in a later wave of the same RUN must return duplicate/not-recorded and must not double-count economics. Replaying the same RUN+turn identity with any conflicting economic evidence must fail closed with the existing different-evidence behavior. Provider UsageEvent identity and provider dedupe semantics must remain unchanged. Preserve unknown_not_zero, exact token semantics, current dirty unrelated files, and current W1 live-control changes. Add or strengthen a discriminating test that creates two waves in one RUN and proves same-receipt dedupe plus conflicting-receipt rejection; include an assertion that provider usage identity still changes across waves as before. No database/framework, no heuristic token inference, no commit/push/restart/package/release/deploy.
- Objective revision: `2`
- Objective SHA-256: `187bb5c203b7326b05ac913827aa89368cbd7160c80d87e078c770f9f2aac99e`
- Objective source: `replan_request`
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
| 33606 | 2026-08-31T18:58:58.600Z | wave_replanned |  | PREFLIGHT | reason=Prior W2 wave reached ACCEPTING with a passing generic test but exact-current acceptance review proved the requested invariant was still false: controller usage_id remained wave-bound and the causal files had no diff/file receipts. The new wave changes both implementation strategy (separate controller economic identity from wave attribution while leaving provider identity unchanged) and oracle (explicit same-RUN cross-wave duplicate + conflict test). |
| 33607 | 2026-08-31T18:58:58.823Z | observation_span_recorded |  |  |  |
| 33608 | 2026-08-31T18:59:00.242Z | observation_span_recorded |  |  |  |
| 33609 | 2026-08-31T18:59:00.533Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 33610 | 2026-08-31T18:59:00.785Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 33611 | 2026-08-31T18:59:01.017Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33612 | 2026-08-31T18:59:01.174Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33613 | 2026-08-31T18:59:01.409Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 33614 | 2026-08-31T18:59:01.616Z | state_transition | READY | ROUTED | reason=route_selected |
| 33615 | 2026-08-31T18:59:01.870Z | observation_span_recorded |  |  |  |
| 33616 | 2026-08-31T18:59:02.732Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f2d21a3e0d3442c48bdb588760cda881 |
| 33617 | 2026-08-31T18:59:02.925Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33618 | 2026-08-31T18:59:03.601Z | observation_span_recorded |  |  |  |
| 33619 | 2026-08-31T18:59:04.008Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f2d21a3e0d3442c48bdb588760cda881 |
| 33620 | 2026-08-31T18:59:04.226Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33621 | 2026-08-31T18:59:04.955Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=7e5737838e14dd9b197982fb8d62bcab75c1e3a8a523a77bf5d888498f85633c |
| 33622 | 2026-08-31T18:59:05.332Z | managed_process_admitted |  |  | owner=default |
| 33623 | 2026-08-31T18:59:05.745Z | managed_process_started |  |  | owner=default |
| 33624 | 2026-08-31T18:59:48.805Z | managed_process_terminal |  |  | owner=default |
| 33625 | 2026-08-31T18:59:49.244Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=7e5737838e14dd9b197982fb8d62bcab75c1e3a8a523a77bf5d888498f85633c |
| 33626 | 2026-08-31T18:59:49.744Z | observation_span_recorded |  |  |  |
| 33627 | 2026-08-31T18:59:49.979Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 33628 | 2026-08-31T18:59:50.219Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 33629 | 2026-08-31T18:59:50.407Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 7e5737838e14dd9b197982fb8d62bcab75c1e3a8a523a77bf5d888498f85633c | False | 43890 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `68eebbb3d4ed53474a066a82e2b7ed4159dd304a63399378475eb04de5050a26`
