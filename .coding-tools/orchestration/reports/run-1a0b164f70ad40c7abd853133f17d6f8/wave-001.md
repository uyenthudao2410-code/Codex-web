# Orchestration Wave 1

- Run: `1a0b164f70ad40c7abd853133f17d6f8`
- Wave: `c4ee03362eda4e5d871499e03da81680`
- Objective: Fix only the nondeterministic timing fixture in the test `new bootstrap terminalizes an expired prior epoch and can create a fresh operation`. Preserve production fail-closed expiry behavior. Replace the 30ms wall-clock TTL plus 40ms sleep with a deterministic Date.now mock: capture original Date.now after RecoveryHost construction, freeze a local `now`, create/update the epoch before expiry, advance `now` past expiry, call prepareBootstrapStart, assert the same FAILED/ACTIVATION_REQUEST_EXPIRED results, and restore Date.now in finally. Do not modify production code or any other dirty file.
- Objective revision: `1`
- Objective SHA-256: `6d6dfa63b9a56f1fbbd9a73aae720c0bb2157a01b3d1b100a346c6078785dd76`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6`
- Worktree fingerprint: `b035b81f9a83619afe666063328eae105fd4c269c893d1f4c8bad8b237d06165`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32208 | 2026-08-28T10:44:20.821Z | run_started |  | PREFLIGHT |  |
| 32209 | 2026-08-28T10:44:21.571Z | observation_span_recorded |  |  |  |
| 32210 | 2026-08-28T10:44:22.723Z | observation_span_recorded |  |  |  |
| 32211 | 2026-08-28T10:44:23.224Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 32212 | 2026-08-28T10:44:23.509Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32213 | 2026-08-28T10:44:23.840Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32214 | 2026-08-28T10:44:24.148Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 32215 | 2026-08-28T10:44:24.553Z | state_transition | READY | ROUTED | reason=route_selected |
| 32216 | 2026-08-28T10:44:24.944Z | observation_span_recorded |  |  |  |
| 32217 | 2026-08-28T10:44:26.424Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c406b3d43bc54863988a16ca855b5e1a |
| 32218 | 2026-08-28T10:44:26.884Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32219 | 2026-08-28T10:44:28.549Z | patch_surface_observed |  |  |  |
| 32220 | 2026-08-28T10:44:29.355Z | observation_span_recorded |  |  |  |
| 32221 | 2026-08-28T10:44:31.858Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c406b3d43bc54863988a16ca855b5e1a |
| 32222 | 2026-08-28T10:44:32.373Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32223 | 2026-08-28T10:44:33.685Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d2c998f07be7a6a5; input_fingerprint=95bccab15209ba1e797ade6ccabd99d8f80a2ea895e4c00b89d17d7e976014a7 |
| 32225 | 2026-08-28T10:44:35.887Z | managed_process_admitted |  |  | owner=default |
| 32226 | 2026-08-28T10:44:36.610Z | managed_process_started |  |  | owner=default |
| 32228 | 2026-08-28T10:44:37.912Z | managed_process_terminal |  |  | owner=default |
| 32229 | 2026-08-28T10:44:38.395Z | proof_recorded |  |  | stage_id=check:d2c998f07be7a6a5; status=passed; cache_hit=False; input_fingerprint=95bccab15209ba1e797ade6ccabd99d8f80a2ea895e4c00b89d17d7e976014a7 |
| 32230 | 2026-08-28T10:44:38.788Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2cedb3b08625ebb84d1cd3473c5addedb55a8899911cec21e99bbd9b9b19aa79 |
| 32231 | 2026-08-28T10:44:39.453Z | managed_process_admitted |  |  | owner=default |
| 32232 | 2026-08-28T10:44:40.096Z | managed_process_started |  |  | owner=default |
| 32233 | 2026-08-28T10:44:41.479Z | managed_process_terminal |  |  | owner=default |
| 32234 | 2026-08-28T10:44:44.288Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2cedb3b08625ebb84d1cd3473c5addedb55a8899911cec21e99bbd9b9b19aa79 |
| 32235 | 2026-08-28T10:44:46.252Z | observation_span_recorded |  |  |  |
| 32236 | 2026-08-28T10:44:47.216Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 32253 | 2026-08-28T10:47:29.181Z | managed_process_admitted |  |  | owner=default |
| 32254 | 2026-08-28T10:47:29.617Z | managed_process_started |  |  | owner=default |
| 32255 | 2026-08-28T10:47:30.354Z | managed_process_terminal |  |  | owner=default |
| 32273 | 2026-08-28T10:47:40.758Z | managed_process_admitted |  |  | owner=default |
| 32274 | 2026-08-28T10:47:41.167Z | managed_process_started |  |  | owner=default |
| 32275 | 2026-08-28T10:47:51.438Z | managed_process_terminal |  |  | owner=default |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d2c998f07be7a6a5 | passed | 95bccab15209ba1e797ade6ccabd99d8f80a2ea895e4c00b89d17d7e976014a7 | False | 4143 | 0 |
| verify:tests | passed | 2cedb3b08625ebb84d1cd3473c5addedb55a8899911cec21e99bbd9b9b19aa79 | False | 4843 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `13aed052c80f758c58a740d58a5263f4307d1d7dfc626fe7eaabe5cba9741333`
