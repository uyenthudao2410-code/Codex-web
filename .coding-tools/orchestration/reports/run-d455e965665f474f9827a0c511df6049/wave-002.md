# Orchestration Wave 2

- Run: `d455e965665f474f9827a0c511df6049`
- Wave: `2d868a31ea5341d29acf39c486aeae3a`
- Objective: Reduce dominant replan/rework causes without changing routing or acceptance policy. Add deterministic caller-patch batch preflight before EOCL run creation so disjoint ambiguous/context-invalid patches fail before any run/write/partial mutation; add bounded candidate line diagnostics for ambiguous hunks; and make agent_workflow/verify_build honor the existing workdir argument for test/build commands. Add focused regressions only. Preserve Smart-v3 tool count, provider gates, EOCL authority, cost-attribution work, and unrelated dirty files. Do not call providers or external review.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `b44ac9c6ef6df9dcbc2aaa5baa6815f7cffe444602be42c9bcb3d6cdaa253153`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4430 | 2026-08-15T05:27:35.138Z | wave_replanned |  | PREFLIGHT | reason=The prior wave reproduced PATCH_CONTEXT_AMBIGUOUS in server.py before any source mutation. This wave materially changes the patch strategy: every server edit is anchored by a unique enclosing function/state block, the helper insertion is anchored immediately before _new_files_patch, and the regression proves future disjoint caller-patch ambiguity fails before a new EOCL run is created. |
| 4431 | 2026-08-15T05:27:35.340Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4432 | 2026-08-15T05:27:35.545Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4433 | 2026-08-15T05:27:35.755Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4434 | 2026-08-15T05:27:35.989Z | state_transition | READY | ROUTED | reason=route_selected |
| 4435 | 2026-08-15T05:27:36.578Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=909ba3a4e0b34081b0ca00f350c9c25e |
| 4436 | 2026-08-15T05:27:36.763Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4437 | 2026-08-15T05:27:37.686Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=909ba3a4e0b34081b0ca00f350c9c25e |
| 4438 | 2026-08-15T05:27:37.895Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4439 | 2026-08-15T05:27:38.414Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3ea29e6034826c8206ac0fe1389e99732018ee253714de4ac92cbcbd6c41b2fd |
| 4440 | 2026-08-15T05:28:05.978Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3ea29e6034826c8206ac0fe1389e99732018ee253714de4ac92cbcbd6c41b2fd |
| 4441 | 2026-08-15T05:28:06.782Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4442 | 2026-08-15T05:28:35.351Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3ea29e6034826c8206ac0fe1389e99732018ee253714de4ac92cbcbd6c41b2fd | False | 27202 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 81bdd4c30b8543ec9c23d428c9ce15a7 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | d34b326eb4feb623e4d500e4f734f51ccf0ea2c4b904526b103fa877d34bc61e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `55361231148c6956011b763cf8d41b4f40c3f1b7ce1bda23e41d634608284996`
