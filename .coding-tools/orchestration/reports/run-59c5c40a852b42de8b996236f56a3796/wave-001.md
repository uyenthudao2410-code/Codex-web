# Orchestration Wave 1

- Run: `59c5c40a852b42de8b996236f56a3796`
- Wave: `bb40ed078f8f4f8cbe6c34c03d9f8cef`
- Objective: Finish pre-EOCL patch-preflight idempotency semantics. Tag every ToolFailure raised by the preflight call, including patch-parse failures before dry-run, as a known no-write terminal outcome; keep all post-preflight exceptions unchanged. Extend the focused regression with malformed patch syntax. No routing, provider, review, restart, or acceptance-policy changes.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `4d2852e795a602cdc9ad3f006a86720164bda2840968826deb3bc902f2c44305`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4456 | 2026-08-15T05:32:59.503Z | run_started |  | PREFLIGHT |  |
| 4457 | 2026-08-15T05:32:59.773Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4458 | 2026-08-15T05:32:59.973Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4459 | 2026-08-15T05:33:00.208Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4460 | 2026-08-15T05:33:00.386Z | state_transition | READY | ROUTED | reason=route_selected |
| 4461 | 2026-08-15T05:33:00.991Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=09c5a51deee644c58e6b82d4b62d51e0 |
| 4462 | 2026-08-15T05:33:01.186Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4463 | 2026-08-15T05:33:01.982Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=09c5a51deee644c58e6b82d4b62d51e0 |
| 4464 | 2026-08-15T05:33:02.158Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4465 | 2026-08-15T05:33:02.671Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c2e75d6db3e4d76594735cae21230edca537205563d1fbf749ae64112b333818 |
| 4466 | 2026-08-15T05:33:34.520Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c2e75d6db3e4d76594735cae21230edca537205563d1fbf749ae64112b333818 |
| 4467 | 2026-08-15T05:33:35.182Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4468 | 2026-08-15T05:33:56.019Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | c2e75d6db3e4d76594735cae21230edca537205563d1fbf749ae64112b333818 | False | 31390 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 30bfe8e8031b4933b7f92d82b9ce7ec0 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 657ad44fa3c4582e9f81d113cb8f32b7f2452cb6bcae4440ab66f3e8b78f0f74 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `8f3679b9329c47c3fc1cacd2ac3e4ccf8664664f25c1e306d23c2c2739880e99`
