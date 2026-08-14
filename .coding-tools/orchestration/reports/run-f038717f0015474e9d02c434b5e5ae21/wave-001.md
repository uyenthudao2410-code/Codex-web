# Orchestration Wave 1

- Run: `f038717f0015474e9d02c434b5e5ae21`
- Wave: `e7434192899245e390f2698aa0285450`
- Objective: Inspect only current candidate-delegation economics persistence and EOCL acceptance metadata needed for Wave 6. Determine whether Codex candidate estimated credits/tokens are stored durably in delegation metadata, and what exact event/checkpoint marks final acceptance. Read-only; no changes.
- Mode: `mcp_only`
- Base HEAD: `62ff046711503260b079e53a85c66e5b9af01e32`
- Worktree fingerprint: `c1c560b0253d8beb2e42feb352591c783138cace23169a843ab3c8eb3a91fc45`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2453 | 2026-08-14T14:35:30.421Z | run_started |  | PREFLIGHT |  |
| 2454 | 2026-08-14T14:35:31.030Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 2455 | 2026-08-14T14:37:28.044Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 2456 | 2026-08-14T14:37:28.120Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2457 | 2026-08-14T14:37:28.194Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2458 | 2026-08-14T14:37:28.319Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2459 | 2026-08-14T14:37:28.411Z | state_transition | READY | ROUTED | reason=route_selected |
| 2460 | 2026-08-14T14:37:28.809Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4b92b07acea34baa91adeb633fe2806f |
| 2461 | 2026-08-14T14:37:28.930Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2462 | 2026-08-14T14:37:29.395Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4b92b07acea34baa91adeb633fe2806f |
| 2463 | 2026-08-14T14:37:29.511Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2464 | 2026-08-14T14:37:38.312Z | proof_recorded |  |  | stage_id=check:12a7b38245e25658; status=passed; cache_hit=False; input_fingerprint=4461ba18923205c28c25de88e882b49f24b2aee1a5b648c510e169335bac8e35 |
| 2465 | 2026-08-14T14:37:38.672Z | proof_recorded |  |  | stage_id=check:af02e2a134203482; status=passed; cache_hit=False; input_fingerprint=7e21806ee18dfc5c744fa37aab7609ba94472e4dd281799ea7246c0894f774f5 |
| 2466 | 2026-08-14T14:37:38.921Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 2467 | 2026-08-14T14:38:27.918Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:12a7b38245e25658 | passed | 4461ba18923205c28c25de88e882b49f24b2aee1a5b648c510e169335bac8e35 | False | 8375 | 0 |
| check:af02e2a134203482 | passed | 7e21806ee18dfc5c744fa37aab7609ba94472e4dd281799ea7246c0894f774f5 | False | 94 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 06c5a38cea1647e28a5713f0cc9a338c | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 | 0ed00495b5e3b844bd0f7894f39445b577f3e82224b5670e41805e8d6a050a2b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `08040cff286d660147319fae53416b24d5b585967153442d16ecf1b8bbb32ddc`
