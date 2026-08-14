# Orchestration Wave 1

- Run: `f16244a44ec9406083cf96bd81d38e51`
- Wave: `dae81cf2f331462298dd00f6e6a8523f`
- Objective: P5: finish routing-v2 evidence without enabling automatic routing. Add model-free similar accepted-route cohorts matched by task_class/workflow, durable warm-thread health from agent lanes, and include both in routing_evidence. Add explicit one-fallback shadow policy metadata (max_fallbacks=1, automatic=false, requires_new_evidence=true) to provider routing recommendations. Preserve shadow_only, mutation_allowed=false, provider admission/EOCL, and public Smart-v3 contract. Add focused tests. No paid provider calls, restart, renderer changes, commit, push, or deploy.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `eea778c6a26fe297fa1ff28943f7bf121d0bef4d80ef2a9927f85fd5cdeca469`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3129 | 2026-08-14T17:38:35.243Z | run_started |  | PREFLIGHT |  |
| 3130 | 2026-08-14T17:38:35.369Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3131 | 2026-08-14T17:38:35.515Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3132 | 2026-08-14T17:38:35.635Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3133 | 2026-08-14T17:38:35.787Z | state_transition | READY | ROUTED | reason=route_selected |
| 3134 | 2026-08-14T17:38:36.232Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4470a3969ca84607a21764ce33412334 |
| 3135 | 2026-08-14T17:38:36.380Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3136 | 2026-08-14T17:38:36.974Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4470a3969ca84607a21764ce33412334 |
| 3137 | 2026-08-14T17:38:37.098Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3138 | 2026-08-14T17:38:37.592Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6368ee1e24d7a04a; input_fingerprint=0361da97ce0b3c9727f41844b0f3b7f11d35aaa5e15f50412a50aad26829f601 |
| 3139 | 2026-08-14T17:38:38.278Z | proof_recorded |  |  | stage_id=check:6368ee1e24d7a04a; status=passed; cache_hit=False; input_fingerprint=0361da97ce0b3c9727f41844b0f3b7f11d35aaa5e15f50412a50aad26829f601 |
| 3140 | 2026-08-14T17:38:38.409Z | proof_cache_miss |  |  | reason=cold; stage_id=check:dfb770765a6c685a; input_fingerprint=05ac5e7e6d75abe7f79a18fdd77254d264113c6de4a9080f125d042af50b17ba |
| 3141 | 2026-08-14T17:38:39.369Z | proof_recorded |  |  | stage_id=check:dfb770765a6c685a; status=passed; cache_hit=False; input_fingerprint=05ac5e7e6d75abe7f79a18fdd77254d264113c6de4a9080f125d042af50b17ba |
| 3142 | 2026-08-14T17:38:40.043Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3143 | 2026-08-14T17:38:54.877Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6368ee1e24d7a04a | passed | 0361da97ce0b3c9727f41844b0f3b7f11d35aaa5e15f50412a50aad26829f601 | False | 340 | 0 |
| check:dfb770765a6c685a | passed | 05ac5e7e6d75abe7f79a18fdd77254d264113c6de4a9080f125d042af50b17ba | False | 749 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3ee28cf930d54d99a877895063f9e27c | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 03bffc3d60117c3556bb294c7d86c6231db1ffe1778470f23154bd0b520d50be | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `1295400daf33f7ba55d7e344c82d4cd07ed204046d2245ad638235d68b747fd4`
