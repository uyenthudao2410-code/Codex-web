# Orchestration Wave 1

- Run: `17eab2d430154178afb96e93a0afa166`
- Wave: `5505e9647da2427aa1035ad3d2ba27df`
- Objective: M1-BOOTSTRAP-EXPIRY-01: stop retrying an expired no-workspace activation bootstrap. Under an atomic activation-state observation, return ACTIVATION_REQUEST_EXPIRED, ok=false, completed=false, retryable=false, workspace_accessed=false and MCP isError=true at or after a positive startup deadline. Preserve the positive pre-deadline bootstrap, no-workspace dispatch boundary, exact receipt/permission/lease checks, already OPEN runtime behavior, max_lines_per_file and the eight public tool schemas. Write only coding_tools_mcp/activation_lifecycle.py, coding_tools_mcp/server.py, tests/test_activation_epoch.py and tests/test_stateless_http_2026.py inside resources/coding-tools-mcp. Preserve all pre-existing WIP. Run focused expiry/HTTP/trace proofs, stop at ACCEPTING, no final acceptance/restart/Git delivery/new product features.
- Objective revision: `1`
- Objective SHA-256: `8bc43905a792c78eef7c0c2ee58ec0e102a5bfa8cafcf21859979fc73326aa88`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `4866cde3d2de7714be300d65052c2c6166b3b2ac8a25ea3476ded937bf16991e`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41098 | 2026-09-06T01:59:54.960Z | run_started |  | PREFLIGHT |  |
| 41099 | 2026-09-06T01:59:55.279Z | observation_span_recorded |  |  |  |
| 41100 | 2026-09-06T01:59:55.518Z | solution_shadow_recommended |  |  |  |
| 41101 | 2026-09-06T01:59:55.683Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41102 | 2026-09-06T01:59:55.902Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41103 | 2026-09-06T01:59:56.176Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 41104 | 2026-09-06T01:59:56.372Z | state_transition | READY | ROUTED | reason=route_selected |
| 41105 | 2026-09-06T01:59:56.614Z | observation_span_recorded |  |  |  |
| 41106 | 2026-09-06T01:59:57.286Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c6cbe595c01243ec8a3501b6ac44f043 |
| 41107 | 2026-09-06T01:59:57.448Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41108 | 2026-09-06T01:59:58.217Z | patch_surface_observed |  |  |  |
| 41109 | 2026-09-06T01:59:58.445Z | observation_span_recorded |  |  |  |
| 41110 | 2026-09-06T01:59:58.796Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c6cbe595c01243ec8a3501b6ac44f043 |
| 41111 | 2026-09-06T01:59:59.100Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41112 | 2026-09-06T01:59:59.578Z | proof_cache_miss |  |  | reason=cold; stage_id=check:695bfd9f1d86a70b; input_fingerprint=e7596e1e79db55eb5a95556e5cf610dfa93731674a675193d2b769114e7a4c3e |
| 41113 | 2026-09-06T01:59:59.985Z | managed_process_admitted |  |  | owner=default |
| 41114 | 2026-09-06T02:00:00.325Z | managed_process_started |  |  | owner=default |
| 41115 | 2026-09-06T02:00:00.860Z | managed_process_terminal |  |  | owner=default |
| 41116 | 2026-09-06T02:00:01.340Z | proof_recorded |  |  | stage_id=check:695bfd9f1d86a70b; status=passed; cache_hit=False; input_fingerprint=e7596e1e79db55eb5a95556e5cf610dfa93731674a675193d2b769114e7a4c3e |
| 41117 | 2026-09-06T02:00:01.593Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=88384db8cfe7b2a2190bab2cea719d2da594732517db003da2c712c3d956fd9d |
| 41118 | 2026-09-06T02:00:01.985Z | managed_process_admitted |  |  | owner=default |
| 41119 | 2026-09-06T02:00:02.418Z | managed_process_started |  |  | owner=default |
| 41120 | 2026-09-06T02:00:10.810Z | managed_process_terminal |  |  | owner=default |
| 41121 | 2026-09-06T02:00:11.237Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=88384db8cfe7b2a2190bab2cea719d2da594732517db003da2c712c3d956fd9d |
| 41122 | 2026-09-06T02:00:12.320Z | observation_span_recorded |  |  |  |
| 41123 | 2026-09-06T02:00:12.537Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41124 | 2026-09-06T02:09:27.208Z | quality_outcome_recorded |  |  |  |
| 41125 | 2026-09-06T02:09:27.400Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41126 | 2026-09-06T02:09:27.672Z | observation_span_recorded |  |  |  |
| 41127 | 2026-09-06T02:09:27.843Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:695bfd9f1d86a70b | passed | e7596e1e79db55eb5a95556e5cf610dfa93731674a675193d2b769114e7a4c3e | False | 1339 | 0 |
| verify:tests | passed | 88384db8cfe7b2a2190bab2cea719d2da594732517db003da2c712c3d956fd9d | False | 9266 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6a8c566faa1d4d8f8c6433af0148f94e | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 077d587c5cd1dcc91d8c6ed940c46404ca30acda15026474dd298aadff3f00f8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `6a78d4b1f9c45c582c13ff0e8a620010ea936a2e4e1e2ba7d4de6281b01da2f3`
