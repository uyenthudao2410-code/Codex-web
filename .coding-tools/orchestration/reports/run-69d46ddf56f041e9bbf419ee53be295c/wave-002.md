# Orchestration Wave 2

- Run: `69d46ddf56f041e9bbf419ee53be295c`
- Wave: `62ff5963b81f4504af8abc2a8b4da640`
- Objective: P3B truthful idempotency gate observability. Keep cumulative PerformanceTrace v5 required coverage unchanged for audit, but introduce a named current auto-key policy epoch 'task_epoch_v1' with fresh required/keyed counters and bounded per-operation breakdown (calls,keyed,missing,missing_reasons). When loading a pre-epoch v5 file, preserve cumulative counters but initialize current-policy counters at zero; never backfill historical misses. Runtime emit_tool_trace must label required operations (agent_workflow:execute, task_control:accept/reject) and missing identity reason when a required key is absent. runtime_activation must report cumulative and current-policy coverage, use current-policy coverage as the decision gate only when the epoch exists, expose target 0.95/pass boolean, and retain legacy-v4 fallback. Add tests proving old 22/30 cumulative history stays intact while a new keyed current-policy sample yields 1.0 current coverage, plus per-operation accounting. No runtime reset/restart or history deletion.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `509f766ea3f44b5470a740af4646d8bc78bbf1920c6427c90841129896b895ed`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3322 | 2026-08-14T18:14:01.195Z | wave_replanned |  | PREFLIGHT | reason=The previous P3B patch was rejected atomically before mutation because one runtime_activation test anchor no longer matched. Split P3B into source telemetry/benchmark plus direct PerformanceTrace test first; update runtime_activation tests in a separate wave using exact current context. No semantic change to the plan. |
| 3323 | 2026-08-14T18:14:01.343Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3324 | 2026-08-14T18:14:01.476Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3325 | 2026-08-14T18:14:01.598Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3326 | 2026-08-14T18:14:01.749Z | state_transition | READY | ROUTED | reason=route_selected |
| 3327 | 2026-08-14T18:14:02.180Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f9048093d37440c6a9308ec6fc4f27cd |
| 3328 | 2026-08-14T18:14:02.322Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3329 | 2026-08-14T18:14:02.931Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f9048093d37440c6a9308ec6fc4f27cd |
| 3330 | 2026-08-14T18:14:03.119Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3331 | 2026-08-14T18:14:03.512Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8b7e9f09a2fb30cc; input_fingerprint=46f50cf89f99e7872f8765cab54e8333a6ba911f30acac99dfcd5b147a033578 |
| 3332 | 2026-08-14T18:14:05.024Z | proof_recorded |  |  | stage_id=check:8b7e9f09a2fb30cc; status=passed; cache_hit=False; input_fingerprint=46f50cf89f99e7872f8765cab54e8333a6ba911f30acac99dfcd5b147a033578 |
| 3333 | 2026-08-14T18:14:05.371Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3334 | 2026-08-14T18:15:05.286Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8b7e9f09a2fb30cc | passed | 46f50cf89f99e7872f8765cab54e8333a6ba911f30acac99dfcd5b147a033578 | False | 1167 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 89c9435485794d3c817a61b1846e7be1 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 1f73c264f82a5ca9808e6a44b4a0167661c71c65667353f2e2c863093ea2e1b6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `b9aeec52ffd3c7db81e8a5c0124c6bae67463eff1779931d0d90eea281915c8b`
