# Orchestration Wave 1

- Run: `625dd5a9698047518dad221e5fb06bd6`
- Wave: `d54307b678a34757a7b29f441bb5dade`
- Objective: Packet C2 controller-mediated bugfix on exact base HEAD 7bc1caee37107a15e74eb078b52fe314e5fa33ab in E:/DEV/Codex-web. Prepare only; do not write a patch, run acceptance, commit, push, restart, or alter .coding-tools evidence. Scope is exactly four paths: resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py, resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py, resources/coding-tools-mcp/tests/test_codex_bridge.py, resources/coding-tools-mcp/tests/test_run_continuation.py. Diagnose and plan the smallest causal fix for exactly two bugs: (1) when _record_notification receives turn/completed before the turn/start response, _launch_turn state.update must not overwrite terminal completed/failed/interrupted state; preserve terminal status, error, token usage, agent_text, finalized, and any existing started_monotonic. (2) revoke/regrant resets policy authorization but currently retains lane_id/thread_id/last_turn_id, so a later start creating a different thread is rejected; after the gate has no pending effect/job and the old grant has no authority, a newly granted policy revision must reset exactly the three dispatch IDs lane_id/thread_id/last_turn_id, without clearing effect history and without bypassing fencing. Plan only focused regressions: three terminal statuses arriving before start response, plus revoke/regrant followed by successful bind of a new thread and verification of the chain. Preserve deadline max30000 and integer schema, observe semantics, permission boundaries, the eight-public-tool contract, all .coding-tools evidence, effect history, and fencing.
- Objective revision: `1`
- Objective SHA-256: `7ffe1dd9f2bf999776834484146018347d4e88e135fc89b65946b005bfd4b4a6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `887ef40a6f16205fb342d2b86864bc7590f7ea919079a44ad729b2514de4342b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43574 | 2026-09-07T23:58:13.711Z | run_started |  | PREFLIGHT |  |
| 43575 | 2026-09-07T23:58:14.027Z | observation_span_recorded |  |  |  |
| 43576 | 2026-09-07T23:58:14.258Z | solution_shadow_recommended |  |  |  |
| 43577 | 2026-09-07T23:58:21.769Z | observation_span_recorded |  |  |  |
| 43578 | 2026-09-07T23:58:21.932Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43579 | 2026-09-08T00:02:40.550Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43580 | 2026-09-08T00:02:40.708Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43581 | 2026-09-08T00:02:40.902Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43582 | 2026-09-08T00:02:41.100Z | state_transition | READY | ROUTED | reason=route_selected |
| 43583 | 2026-09-08T00:02:41.308Z | observation_span_recorded |  |  |  |
| 43584 | 2026-09-08T00:02:42.104Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9aedfbef606448319b0f84a88e58abef |
| 43585 | 2026-09-08T00:02:42.259Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43586 | 2026-09-08T00:02:43.207Z | patch_surface_observed |  |  |  |
| 43587 | 2026-09-08T00:02:43.413Z | observation_span_recorded |  |  |  |
| 43588 | 2026-09-08T00:02:43.685Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9aedfbef606448319b0f84a88e58abef |
| 43589 | 2026-09-08T00:02:43.853Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43590 | 2026-09-08T00:02:44.604Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8b9407bc23abeeb5; input_fingerprint=8abce8b3253fe04d1c58aefaa2457d279ee034e0742b988e7465ddaac8c75540 |
| 43591 | 2026-09-08T00:02:45.052Z | managed_process_admitted |  |  | owner=default |
| 43592 | 2026-09-08T00:02:45.418Z | managed_process_started |  |  | owner=default |
| 43593 | 2026-09-08T00:02:55.877Z | managed_process_terminal |  |  | owner=default |
| 43594 | 2026-09-08T00:02:56.274Z | proof_recorded |  |  | stage_id=check:8b9407bc23abeeb5; status=passed; cache_hit=False; input_fingerprint=8abce8b3253fe04d1c58aefaa2457d279ee034e0742b988e7465ddaac8c75540 |
| 43595 | 2026-09-08T00:02:56.460Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3599fb76d8389bab; input_fingerprint=8dab9ed22622199795665c8868263450b94862fe626cdca988bfa1abc429712b |
| 43596 | 2026-09-08T00:02:56.785Z | managed_process_admitted |  |  | owner=default |
| 43597 | 2026-09-08T00:02:57.112Z | managed_process_started |  |  | owner=default |
| 43598 | 2026-09-08T00:02:57.636Z | managed_process_terminal |  |  | owner=default |
| 43599 | 2026-09-08T00:02:57.944Z | proof_recorded |  |  | stage_id=check:3599fb76d8389bab; status=passed; cache_hit=False; input_fingerprint=8dab9ed22622199795665c8868263450b94862fe626cdca988bfa1abc429712b |
| 43600 | 2026-09-08T00:02:58.133Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=249d3354cda844754f21148894cce3c2bac6c8163f2aaea7eadd3e937d01cac4 |
| 43601 | 2026-09-08T00:02:58.495Z | managed_process_admitted |  |  | owner=default |
| 43602 | 2026-09-08T00:02:58.802Z | managed_process_started |  |  | owner=default |
| 43603 | 2026-09-08T00:02:59.236Z | managed_process_terminal |  |  | owner=default |
| 43604 | 2026-09-08T00:02:59.572Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=249d3354cda844754f21148894cce3c2bac6c8163f2aaea7eadd3e937d01cac4 |
| 43605 | 2026-09-08T00:02:59.808Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=de89200fca89ad3440860cbe01424e69c1026d02cafd8c7f2f7cd29e06b00490 |
| 43606 | 2026-09-08T00:03:00.193Z | managed_process_admitted |  |  | owner=default |
| 43607 | 2026-09-08T00:03:00.560Z | managed_process_started |  |  | owner=default |
| 43608 | 2026-09-08T00:03:01.361Z | managed_process_terminal |  |  | owner=default |
| 43609 | 2026-09-08T00:03:01.712Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=de89200fca89ad3440860cbe01424e69c1026d02cafd8c7f2f7cd29e06b00490 |
| 43610 | 2026-09-08T00:03:02.637Z | observation_span_recorded |  |  |  |
| 43611 | 2026-09-08T00:03:02.873Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43612 | 2026-09-08T00:06:31.556Z | quality_outcome_recorded |  |  |  |
| 43613 | 2026-09-08T00:06:31.764Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43614 | 2026-09-08T00:06:32.105Z | observation_span_recorded |  |  |  |
| 43615 | 2026-09-08T00:06:32.292Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8b9407bc23abeeb5 | passed | 8abce8b3253fe04d1c58aefaa2457d279ee034e0742b988e7465ddaac8c75540 | False | 11311 | 0 |
| check:3599fb76d8389bab | passed | 8dab9ed22622199795665c8868263450b94862fe626cdca988bfa1abc429712b | False | 1192 | 0 |
| check:80a1a46bd01d26a3 | passed | 249d3354cda844754f21148894cce3c2bac6c8163f2aaea7eadd3e937d01cac4 | False | 1093 | 0 |
| check:466c2f308b48c766 | passed | de89200fca89ad3440860cbe01424e69c1026d02cafd8c7f2f7cd29e06b00490 | False | 1520 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3e302f65288441a09af8daff77656e3f | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 63e909230298c4138ad33aa821d02728ff15a2f5b0ae5f98a970d12c1a38da58 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `90fdb16dcc84dba61f59656c67cd0bd7c01b1b480e02357f48b8ec8bf017983a`
