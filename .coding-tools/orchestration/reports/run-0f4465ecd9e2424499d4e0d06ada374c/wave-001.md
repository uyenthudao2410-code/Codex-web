# Orchestration Wave 1

- Run: `0f4465ecd9e2424499d4e0d06ada374c`
- Wave: `721404f5437f4dc9925717e54fc969a5`
- Objective: P5B test-only closure for the accepted Python native Rust semantic provider. Add negative regression coverage proving drive-letter absolute semantic scopes are rejected before transport, top-level ok=false responses fail closed even when data resembles the expected contract, and symlink credential files are rejected when symlink creation is supported. Do not change production source, routing gates, live activation, restart, providers, commit, or push.
- Mode: `mcp_only`
- Base HEAD: `e45bed968bee6db46bb3041de179cbcf23e3906b`
- Worktree fingerprint: `640d3b78aa13536087c78e58b8d2fe95a2fba13012553b75177b69955af3bfc2`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3540 | 2026-08-14T22:56:29.050Z | run_started |  | PREFLIGHT |  |
| 3541 | 2026-08-14T22:56:29.172Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3542 | 2026-08-14T22:56:29.306Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3543 | 2026-08-14T22:56:29.429Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3544 | 2026-08-14T22:56:29.530Z | state_transition | READY | ROUTED | reason=route_selected |
| 3545 | 2026-08-14T22:56:29.939Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5e118a2d0ffd41f9ab3403cb02162783 |
| 3546 | 2026-08-14T22:56:30.058Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3547 | 2026-08-14T22:56:30.530Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5e118a2d0ffd41f9ab3403cb02162783 |
| 3548 | 2026-08-14T22:56:30.655Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3549 | 2026-08-14T22:56:30.986Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:122bf4dfd3a03297; input_fingerprint=3bcb65b7deb690d761452931c4a2bf1fcc5d0b996820c3df75e63353ee8a8fa5 |
| 3550 | 2026-08-14T22:56:31.521Z | proof_recorded |  |  | stage_id=check:122bf4dfd3a03297; status=passed; cache_hit=False; input_fingerprint=3bcb65b7deb690d761452931c4a2bf1fcc5d0b996820c3df75e63353ee8a8fa5 |
| 3551 | 2026-08-14T22:56:31.700Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6a6bacb05e636d1a; input_fingerprint=0dbc058ba92335f6518bff8f284ab246242a791bd4eb655ad5b5f44e8410e83d |
| 3552 | 2026-08-14T22:56:33.048Z | proof_recorded |  |  | stage_id=check:6a6bacb05e636d1a; status=passed; cache_hit=False; input_fingerprint=0dbc058ba92335f6518bff8f284ab246242a791bd4eb655ad5b5f44e8410e83d |
| 3553 | 2026-08-14T22:56:33.200Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=b97a84a632d82006e8a1c311df7defc3c2f0e109320ae7892d6480a24a9f0c14 |
| 3554 | 2026-08-14T22:56:33.739Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=b97a84a632d82006e8a1c311df7defc3c2f0e109320ae7892d6480a24a9f0c14 |
| 3555 | 2026-08-14T22:56:33.880Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2b3a4e55a3b1c2e5da58a2ea26bd90fd08545b6b1676c3a609bd278208d72fa0 |
| 3556 | 2026-08-14T22:56:37.659Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2b3a4e55a3b1c2e5da58a2ea26bd90fd08545b6b1676c3a609bd278208d72fa0 |
| 3557 | 2026-08-14T22:56:37.949Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:122bf4dfd3a03297 | passed | 3bcb65b7deb690d761452931c4a2bf1fcc5d0b996820c3df75e63353ee8a8fa5 | False | 284 | 0 |
| check:6a6bacb05e636d1a | passed | 0dbc058ba92335f6518bff8f284ab246242a791bd4eb655ad5b5f44e8410e83d | False | 1065 | 0 |
| check:466c2f308b48c766 | passed | b97a84a632d82006e8a1c311df7defc3c2f0e109320ae7892d6480a24a9f0c14 | False | 289 | 0 |
| verify:tests | passed | 2b3a4e55a3b1c2e5da58a2ea26bd90fd08545b6b1676c3a609bd278208d72fa0 | False | 3438 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `b0f40ff6dead0444188eed7ba8e07a12f46a5232b2ee17e5ba8cb45188b90abc`
