# Orchestration Wave 1

- Run: `accb98f48c2941c9a9b031bc8b79b0a2`
- Wave: `bc477635dbcf4525b76b2cd6db857007`
- Objective: Close the F4/F6 real-process tunnel recovery proof gap with an explicit test-only patch. Add a Node-based tunnel fixture whose run process owns the real loopback health listener and whose health command validates the exact expected PID without any external network. Add F4 Recovery Plane proof that killing only Recovery Tunnel produces a new tunnel PID while Recovery MCP PID/device identity/ports remain unchanged. Add F6 primary RuntimeOrchestrator proof that recoverTunnelOnly replaces only the primary Tunnel while the real Coding MCP process/workspace/device identity remains unchanged, using a loopback-only manual proxy. Do not modify production source or unrelated dirty files.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `31bc071cde98ba9365c033eb8558bfae18c253f9ab0e84d539f865df1a2cd4a2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13670 | 2026-08-17T11:03:41.528Z | run_started |  | PREFLIGHT |  |
| 13671 | 2026-08-17T11:03:42.231Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13672 | 2026-08-17T11:03:42.461Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13673 | 2026-08-17T11:03:42.718Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13674 | 2026-08-17T11:03:42.901Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13675 | 2026-08-17T11:03:43.040Z | state_transition | READY | ROUTED | reason=route_selected |
| 13676 | 2026-08-17T11:03:43.742Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7497e8222595403ea287ccc4278bad73 |
| 13677 | 2026-08-17T11:03:43.914Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13678 | 2026-08-17T11:03:44.650Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7497e8222595403ea287ccc4278bad73 |
| 13679 | 2026-08-17T11:03:44.831Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13680 | 2026-08-17T11:03:45.565Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:2f4546c29a84a03e; input_fingerprint=0de8f521344ae1787526ed2ecd23058a859920015ff03cc6093ce19ca3cde574 |
| 13681 | 2026-08-17T11:03:45.912Z | managed_process_admitted |  |  | owner=default |
| 13682 | 2026-08-17T11:03:46.135Z | managed_process_started |  |  | owner=default |
| 13683 | 2026-08-17T11:03:46.650Z | managed_process_terminal |  |  | owner=default |
| 13684 | 2026-08-17T11:03:46.944Z | proof_recorded |  |  | stage_id=check:2f4546c29a84a03e; status=passed; cache_hit=False; input_fingerprint=0de8f521344ae1787526ed2ecd23058a859920015ff03cc6093ce19ca3cde574 |
| 13685 | 2026-08-17T11:03:47.119Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a94f184fad00be520a63253915c8fe1a1e9e9516a23f515e8c5e663c1bba1186 |
| 13686 | 2026-08-17T11:03:47.507Z | managed_process_admitted |  |  | owner=default |
| 13687 | 2026-08-17T11:03:47.802Z | managed_process_started |  |  | owner=default |
| 13688 | 2026-08-17T11:03:53.593Z | managed_process_terminal |  |  | owner=default |
| 13689 | 2026-08-17T11:03:54.985Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a94f184fad00be520a63253915c8fe1a1e9e9516a23f515e8c5e663c1bba1186 |
| 13690 | 2026-08-17T11:03:55.715Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13691 | 2026-08-17T11:04:51.617Z | managed_process_admitted |  |  | owner=chatweb |
| 13692 | 2026-08-17T11:04:51.944Z | managed_process_started |  |  | owner=chatweb |
| 13693 | 2026-08-17T11:04:52.560Z | managed_process_terminal |  |  | owner=chatweb |
| 13694 | 2026-08-17T11:05:09.901Z | managed_process_admitted |  |  | owner=chatweb |
| 13695 | 2026-08-17T11:05:10.251Z | managed_process_started |  |  | owner=chatweb |
| 13696 | 2026-08-17T11:05:15.057Z | managed_process_terminal |  |  | owner=chatweb |
| 13697 | 2026-08-17T11:05:46.507Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13698 | 2026-08-17T11:05:47.047Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2f4546c29a84a03e | passed | 0de8f521344ae1787526ed2ecd23058a859920015ff03cc6093ce19ca3cde574 | False | 1081 | 0 |
| verify:tests | passed | a94f184fad00be520a63253915c8fe1a1e9e9516a23f515e8c5e663c1bba1186 | False | 7328 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bc9cc4ca25cb40d191c4882c98c60373 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 74284b4c64d0c4cdee06d460fa7944f50ee0012db1e3f8fcb2b9f16f129fd0db | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `bd441ed7820a1dd6b941667188e7e33eee7de3604a6ee8ee274f485fc057ba2a`
