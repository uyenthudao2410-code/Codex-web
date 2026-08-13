# Orchestration Wave 1

- Run: `2ebe1c011dd44e7189f7ae71f0c9b1a8`
- Wave: `e9bf0f3b730f4dc89bfae20dfe6bdfb1`
- Objective: Make the Ubuntu canonical Rust gate diagnosable without weakening it. Preserve the exact cargo test --locked --workspace command and its exit status, tee its complete output to cargo-test.log, write a compact failure excerpt to GITHUB_STEP_SUMMARY / GitHub error annotations when it fails, and upload cargo-test.log as a short-retention artifact only on failure. This is release-proof observability so the exact failing Rust test/panic can be retrieved on the next CI run. Do not change Rust code or test selection.
- Mode: `mcp_only`
- Base HEAD: `bb8ccdcb87a13afc4c4d3a99b756cf821dfcfe72`
- Worktree fingerprint: `c45674a4f0be82f7d296b0145f5a1ef81a0b3de88e1d2427923b01974e4019eb`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 490 | 2026-08-13T17:56:11.207Z | run_started |  | PREFLIGHT |  |
| 491 | 2026-08-13T17:56:11.518Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 492 | 2026-08-13T17:56:11.698Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 493 | 2026-08-13T17:56:11.802Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 494 | 2026-08-13T17:56:11.923Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 495 | 2026-08-13T17:56:12.022Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 496 | 2026-08-13T17:56:12.139Z | state_transition | READY | ROUTED | reason=route_selected |
| 497 | 2026-08-13T17:56:12.459Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=70754237930f4bd89235d7ff5aec8562 |
| 498 | 2026-08-13T17:56:12.556Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 499 | 2026-08-13T17:56:12.914Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=70754237930f4bd89235d7ff5aec8562 |
| 500 | 2026-08-13T17:56:13.006Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 501 | 2026-08-13T17:56:13.433Z | proof_recorded |  |  | stage_id=check:d3678d4e379afac1; status=passed; cache_hit=False; input_fingerprint=06acde2c12ef06db0632795b1bbb0e65e05b080fa1ce3c1cff9cd431922b183c |
| 502 | 2026-08-13T17:56:13.974Z | proof_recorded |  |  | stage_id=check:aa6d51931ad29c1c; status=passed; cache_hit=False; input_fingerprint=109153db827524ab4aeb509a77f96edeb7a2d04584788f3c9eb681a16b8da849 |
| 503 | 2026-08-13T17:56:16.530Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=d8e09893689156154e03adb0a4c56e55d84abe19f8d309555e019fe3ade0cc5a |
| 504 | 2026-08-13T17:56:24.877Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d3678d4e379afac1 | passed | 06acde2c12ef06db0632795b1bbb0e65e05b080fa1ce3c1cff9cd431922b183c | False | 85 | 0 |
| check:aa6d51931ad29c1c | passed | 109153db827524ab4aeb509a77f96edeb7a2d04584788f3c9eb681a16b8da849 | False | 328 | 0 |
| verify:tests | passed | d8e09893689156154e03adb0a4c56e55d84abe19f8d309555e019fe3ade0cc5a | False | 2359 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `afbf1e7234e387bcb92f183978167e7fa5caedbee8e3c586527dc0cdf45d551a`
