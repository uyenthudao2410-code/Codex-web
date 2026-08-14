# Orchestration Wave 1

- Run: `4efb680c2b9e4799afc62d5ed21658ce`
- Wave: `781c285eb9ef482486f901e90826e7d6`
- Objective: Project the already-accepted proof-cache observability metrics into the existing machine-readable runtime activation benchmark snapshot. Add proof_cache_eligible, proof_cache_misses, proof_cache_miss_reasons alongside existing hits/saved_ms and update the focused snapshot test. Do not change snapshot schema_version, runtime behavior, Smart-v3/public schemas, proof reuse semantics, routing, or safety boundaries. No paid calls, restart, deploy, commit, or push.
- Mode: `mcp_only`
- Base HEAD: `62ff046711503260b079e53a85c66e5b9af01e32`
- Worktree fingerprint: `943fdd478b10f620eded4651c6f28b3e1dd17ff4c19eded2fb284ea1fc31625c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2609 | 2026-08-14T15:50:47.052Z | run_started |  | PREFLIGHT |  |
| 2610 | 2026-08-14T15:50:47.518Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 2611 | 2026-08-14T15:50:47.677Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2612 | 2026-08-14T15:50:47.819Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2613 | 2026-08-14T15:50:47.967Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2614 | 2026-08-14T15:50:48.086Z | state_transition | READY | ROUTED | reason=route_selected |
| 2615 | 2026-08-14T15:50:48.468Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d79e95ba5bb64133b3924ecbab86c81f |
| 2616 | 2026-08-14T15:50:48.617Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2617 | 2026-08-14T15:50:49.226Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d79e95ba5bb64133b3924ecbab86c81f |
| 2618 | 2026-08-14T15:50:49.343Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2619 | 2026-08-14T15:50:53.577Z | proof_recorded |  |  | stage_id=check:d0f94e786c90001f; status=passed; cache_hit=False; input_fingerprint=58271b2b11815ce1e0cea2d7dff995c6cd248423d4427c3d080d82e2f505545b |
| 2620 | 2026-08-14T15:50:53.927Z | proof_recorded |  |  | stage_id=check:1e245b18ad2c26dd; status=passed; cache_hit=False; input_fingerprint=ab3107af44cd47837fb285ea16bdda4c0378be9513125c1725f671471e61b2c7 |
| 2621 | 2026-08-14T15:51:02.822Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 2622 | 2026-08-14T15:51:15.808Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d0f94e786c90001f | passed | 58271b2b11815ce1e0cea2d7dff995c6cd248423d4427c3d080d82e2f505545b | False | 3596 | 0 |
| check:1e245b18ad2c26dd | passed | ab3107af44cd47837fb285ea16bdda4c0378be9513125c1725f671471e61b2c7 | False | 127 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fc6f47d58cef432288aef5480330e975 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 | c4467d16dc3a9e02c64d4fd98c309e0ae5b438a3e5b71c2ea8cd3a49d552ae40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `27acc0d199a020268c0aef2443836870768468525d86acfd8a630fb1a4b5061a`
