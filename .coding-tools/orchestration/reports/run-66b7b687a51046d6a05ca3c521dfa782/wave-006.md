# Orchestration Wave 6

- Run: `66b7b687a51046d6a05ca3c521dfa782`
- Wave: `a346e197e9c74aa680c5b2c7e9929b45`
- Objective: Replan Phase 3B after 37/38 focused tests passed but the standalone Recovery MCP test parsed an unexpected HTML response on the dynamically allocated port. Strengthen only the process oracle first: capture the spawned Recovery MCP stderr, require the child PID to still be alive after TCP readiness, GET /healthz from the same port and assert service='recovery-mcp' and pid==child.pid before making authenticated MCP requests. Make the generic HTTP helper preserve raw non-JSON bodies in assertion errors instead of throwing JSON.parse. Do not weaken Recovery MCP production behavior or auth assertions. Rerun py_compile and focused recovery-plane test.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `d6a56e366b3ef8dc3d27b904e5a8a5f3a79c3f00438f02b7692b2e7a29191566`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6684 | 2026-08-16T09:06:13.468Z | wave_replanned |  | PREFLIGHT | reason=The previous acceptance was rejected because canonical receipts still omitted Recovery MCP Python, and review found a stale Recovery Tunnel lifecycle gap: invalidating tunnel configuration could leave the old service-owned remote endpoint alive. This wave changes both evidence scope and safety behavior before activation. |
| 6685 | 2026-08-16T09:06:15.056Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6686 | 2026-08-16T09:06:16.451Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6687 | 2026-08-16T09:06:17.465Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6688 | 2026-08-16T09:06:18.649Z | state_transition | READY | ROUTED | reason=route_selected |
| 6689 | 2026-08-16T09:06:21.309Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e995b7ba2f27439e8430606b0d6f75c5 |
| 6690 | 2026-08-16T09:06:23.444Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6691 | 2026-08-16T09:06:27.310Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e995b7ba2f27439e8430606b0d6f75c5 |
| 6692 | 2026-08-16T09:06:28.676Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6693 | 2026-08-16T09:06:31.992Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:25606f562d597b39; input_fingerprint=603ccce76f859b2dc555929b808201fa6c6259f386ef3cee30f2e8e6e5c48e8a |
| 6694 | 2026-08-16T09:06:38.071Z | managed_process_admitted |  |  | owner=default |
| 6695 | 2026-08-16T09:06:42.621Z | managed_process_started |  |  | owner=default |
| 6696 | 2026-08-16T09:06:45.464Z | managed_process_terminal |  |  | owner=default |
| 6697 | 2026-08-16T09:06:48.242Z | proof_recorded |  |  | stage_id=check:25606f562d597b39; status=passed; cache_hit=False; input_fingerprint=603ccce76f859b2dc555929b808201fa6c6259f386ef3cee30f2e8e6e5c48e8a |
| 6698 | 2026-08-16T09:06:50.088Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:45c86d0688b3516a; input_fingerprint=85e542b27642050253bb5fa300ff3f089a2bfeb0ed7f0e33446ce06701f32ece |
| 6699 | 2026-08-16T09:06:54.045Z | managed_process_admitted |  |  | owner=default |
| 6700 | 2026-08-16T09:06:57.401Z | managed_process_started |  |  | owner=default |
| 6701 | 2026-08-16T09:06:59.634Z | managed_process_terminal |  |  | owner=default |
| 6702 | 2026-08-16T09:07:02.248Z | proof_recorded |  |  | stage_id=check:45c86d0688b3516a; status=passed; cache_hit=False; input_fingerprint=85e542b27642050253bb5fa300ff3f089a2bfeb0ed7f0e33446ce06701f32ece |
| 6703 | 2026-08-16T09:07:04.587Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=f7d2ab0e86a0f74b0966d9dd9bb9168ceb0bb4d3aa6accc2151549fcd4e394e3 |
| 6704 | 2026-08-16T09:07:10.209Z | managed_process_admitted |  |  | owner=default |
| 6705 | 2026-08-16T09:07:13.334Z | managed_process_started |  |  | owner=default |
| 6706 | 2026-08-16T09:07:30.355Z | managed_process_terminal |  |  | owner=default |
| 6707 | 2026-08-16T09:07:34.406Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=passed; cache_hit=False; input_fingerprint=f7d2ab0e86a0f74b0966d9dd9bb9168ceb0bb4d3aa6accc2151549fcd4e394e3 |
| 6708 | 2026-08-16T09:07:37.621Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2afe15d6f32bb02b; input_fingerprint=1ea8c95cd038cac6dad3b2cf35d3039075a27d468ad776bef5b5288f1e054091 |
| 6709 | 2026-08-16T09:07:40.531Z | managed_process_admitted |  |  | owner=default |
| 6710 | 2026-08-16T09:07:44.472Z | managed_process_started |  |  | owner=default |
| 6711 | 2026-08-16T09:07:53.511Z | managed_process_terminal |  |  | owner=default |
| 6712 | 2026-08-16T09:07:56.692Z | proof_recorded |  |  | stage_id=check:2afe15d6f32bb02b; status=passed; cache_hit=False; input_fingerprint=1ea8c95cd038cac6dad3b2cf35d3039075a27d468ad776bef5b5288f1e054091 |
| 6713 | 2026-08-16T09:07:58.943Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=691c51de16f4453ab1e3f94400940c54ca1d64f91b0b9d2cb417681d027f1f79 |
| 6714 | 2026-08-16T09:08:03.120Z | managed_process_admitted |  |  | owner=default |
| 6715 | 2026-08-16T09:08:06.554Z | managed_process_started |  |  | owner=default |
| 6716 | 2026-08-16T09:08:17.740Z | managed_process_terminal |  |  | owner=default |
| 6717 | 2026-08-16T09:08:20.390Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=691c51de16f4453ab1e3f94400940c54ca1d64f91b0b9d2cb417681d027f1f79 |
| 6718 | 2026-08-16T09:08:22.126Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6719 | 2026-08-16T09:10:06.862Z | failure_observed | ACCEPTING | ACCEPTING | reason=Behavior/proof is green, but task-state still does not list resources/recovery-mcp/recovery_mcp.py in modified_files after the background workflow completed. Do not accept a checkpoint that cannot issue a canonical receipt for the Recovery MCP runtime. Replan one small Recovery-MCP-only contract wave that adds a useful snapshot schema marker and records the Python path explicitly; reuse prior green JS/service proof only where source is unchanged.; failure_class=SOL_REJECTED |
| 6720 | 2026-08-16T09:10:08.623Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 6721 | 2026-08-16T09:10:14.547Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:25606f562d597b39 | passed | 603ccce76f859b2dc555929b808201fa6c6259f386ef3cee30f2e8e6e5c48e8a | False | 13574 | 0 |
| check:45c86d0688b3516a | passed | 85e542b27642050253bb5fa300ff3f089a2bfeb0ed7f0e33446ce06701f32ece | False | 9945 | 0 |
| check:328e123c63857fd8 | passed | f7d2ab0e86a0f74b0966d9dd9bb9168ceb0bb4d3aa6accc2151549fcd4e394e3 | False | 25493 | 0 |
| check:2afe15d6f32bb02b | passed | 1ea8c95cd038cac6dad3b2cf35d3039075a27d468ad776bef5b5288f1e054091 | False | 16243 | 0 |
| verify:tests | passed | 691c51de16f4453ab1e3f94400940c54ca1d64f91b0b9d2cb417681d027f1f79 | False | 19203 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `271`
- Chain head: `6e3848c269d200d6fca4d0162b782332078ef865e4cd623aea8368f5fef0422d`
