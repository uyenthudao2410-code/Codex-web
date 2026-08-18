# Orchestration Wave 1

- Run: `f7509bb6172a447e94ddd0a2f90770c1`
- Wave: `b256fbc22fb54964b0151f91329c044e`
- Objective: Add focused integration regression coverage for the now-accepted explicit validation compute-placement runtime. Extend the existing internal R3B2 harness only: prove server_preferred clean dispatch to an eligible server-compute Runner with durable/handoff/status/log evidence; local_only stays on the source Runner even when a server target is eligible; server_preferred safely falls back to source with fallback evidence; dirty, sandboxed, and short explicit contexts reject before any enqueue. Keep the existing selector-absent dirty snapshot scenarios unchanged so they prove default production routing regression. Run rustfmt, the feature-gated R3B2 integration test, git diff check, and affected webcodex package check. No analyzer/manifest/restart/P3 enrollment.
- Mode: `mcp_only`
- Base HEAD: `17e87d34b159cbc175a77bb041e670000c9f7f4b`
- Worktree fingerprint: `c8f4099ce12fe2a0e82e8dceb0abd12d3d558911e994f88ef6eaa1f899995a5d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16412 | 2026-08-18T00:35:53.981Z | run_started |  | PREFLIGHT |  |
| 16413 | 2026-08-18T00:35:54.386Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16414 | 2026-08-18T00:35:54.512Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16415 | 2026-08-18T00:35:54.641Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16416 | 2026-08-18T00:35:54.754Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16417 | 2026-08-18T00:35:54.979Z | state_transition | READY | ROUTED | reason=route_selected |
| 16418 | 2026-08-18T00:35:55.406Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cf738fbdab584fcc93b573f8fc23527d |
| 16419 | 2026-08-18T00:35:55.522Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16420 | 2026-08-18T00:35:56.022Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cf738fbdab584fcc93b573f8fc23527d |
| 16421 | 2026-08-18T00:35:56.148Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16422 | 2026-08-18T00:35:56.509Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:718b79fbd1bef7b9; input_fingerprint=eb7bde10eaeb8ea50c8e1e08714673c83a483b7e663695a5203711d0402604f9 |
| 16423 | 2026-08-18T00:35:56.772Z | managed_process_admitted |  |  | owner=default |
| 16424 | 2026-08-18T00:35:56.981Z | managed_process_started |  |  | owner=default |
| 16425 | 2026-08-18T00:36:04.164Z | managed_process_terminal |  |  | owner=default |
| 16426 | 2026-08-18T00:36:04.506Z | proof_recorded |  |  | stage_id=check:718b79fbd1bef7b9; status=passed; cache_hit=False; input_fingerprint=eb7bde10eaeb8ea50c8e1e08714673c83a483b7e663695a5203711d0402604f9 |
| 16427 | 2026-08-18T00:36:04.636Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=6bd1849f55487ebe2d7dd475d7562dd8f34e4480e96a559f08af8907c89c2e6b |
| 16428 | 2026-08-18T00:36:04.864Z | managed_process_admitted |  |  | owner=default |
| 16429 | 2026-08-18T00:36:05.073Z | managed_process_started |  |  | owner=default |
| 16430 | 2026-08-18T00:36:10.584Z | managed_process_terminal |  |  | owner=default |
| 16431 | 2026-08-18T00:36:10.799Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=6bd1849f55487ebe2d7dd475d7562dd8f34e4480e96a559f08af8907c89c2e6b |
| 16432 | 2026-08-18T00:36:10.917Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8a2e102ca3867991; input_fingerprint=4d40ebc40dea17ba9d938c9f68d445933abc2dd8fb3dc04462a55d0f1c2f9fee |
| 16433 | 2026-08-18T00:36:11.265Z | managed_process_admitted |  |  | owner=default |
| 16434 | 2026-08-18T00:36:11.481Z | managed_process_started |  |  | owner=default |
| 16435 | 2026-08-18T00:39:36.936Z | managed_process_terminal |  |  | owner=default |
| 16436 | 2026-08-18T00:39:37.294Z | proof_recorded |  |  | stage_id=check:8a2e102ca3867991; status=passed; cache_hit=False; input_fingerprint=4d40ebc40dea17ba9d938c9f68d445933abc2dd8fb3dc04462a55d0f1c2f9fee |
| 16437 | 2026-08-18T00:39:37.530Z | proof_cache_miss |  |  | reason=cold; stage_id=check:53ba03fece826296; input_fingerprint=0c3d5b50562f3f2dc81bc84e1044d81ab3c21888092224c37dd4ba41191f5c10 |
| 16438 | 2026-08-18T00:39:37.895Z | managed_process_admitted |  |  | owner=default |
| 16439 | 2026-08-18T00:39:38.347Z | managed_process_started |  |  | owner=default |
| 16440 | 2026-08-18T00:39:38.987Z | managed_process_terminal |  |  | owner=default |
| 16441 | 2026-08-18T00:39:39.363Z | proof_recorded |  |  | stage_id=check:53ba03fece826296; status=passed; cache_hit=False; input_fingerprint=0c3d5b50562f3f2dc81bc84e1044d81ab3c21888092224c37dd4ba41191f5c10 |
| 16442 | 2026-08-18T00:39:39.605Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:586ac65f8024ef3b; input_fingerprint=e5dde39d7e71326e1c75efccd28ea7477f5b84c03377164429743adcd58da58e |
| 16443 | 2026-08-18T00:39:40.014Z | managed_process_admitted |  |  | owner=default |
| 16444 | 2026-08-18T00:39:40.329Z | managed_process_started |  |  | owner=default |
| 16445 | 2026-08-18T00:39:41.638Z | managed_process_terminal |  |  | owner=default |
| 16446 | 2026-08-18T00:39:41.966Z | proof_recorded |  |  | stage_id=check:586ac65f8024ef3b; status=passed; cache_hit=False; input_fingerprint=e5dde39d7e71326e1c75efccd28ea7477f5b84c03377164429743adcd58da58e |
| 16447 | 2026-08-18T00:39:42.562Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16448 | 2026-08-18T00:40:07.484Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 16449 | 2026-08-18T00:40:07.757Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:718b79fbd1bef7b9 | passed | eb7bde10eaeb8ea50c8e1e08714673c83a483b7e663695a5203711d0402604f9 | False | 7692 | 0 |
| check:810e75f0d3dee10e | passed | 6bd1849f55487ebe2d7dd475d7562dd8f34e4480e96a559f08af8907c89c2e6b | False | 5972 | 0 |
| check:8a2e102ca3867991 | passed | 4d40ebc40dea17ba9d938c9f68d445933abc2dd8fb3dc04462a55d0f1c2f9fee | False | 206077 | 0 |
| check:53ba03fece826296 | passed | 0c3d5b50562f3f2dc81bc84e1044d81ab3c21888092224c37dd4ba41191f5c10 | False | 1549 | 0 |
| check:586ac65f8024ef3b | passed | e5dde39d7e71326e1c75efccd28ea7477f5b84c03377164429743adcd58da58e | False | 2060 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 36dd26e37632418989252cfc1614e05f | accepted | 17e87d34b159cbc175a77bb041e670000c9f7f4b | 57e512c5719a3cec339b4b303e1c6f9404a413b0fb0e937347de366f4a4bd59a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `afcbff15040eedc996b18dd373dd70dbf12b968b261c1ffd86fbaea7204d6e01`
