# Orchestration Wave 1

- Run: `58ee3edebd6c44faad7b7a4aecf48391`
- Wave: `73dd5d0924434e90aef561a0a6a00bcb`
- Objective: Fix the P3 organic host-turn correlation race proven in Electron evaluation handling. A staged user_turn_visible correlation record must remain available for MCP to claim until the corresponding host_turn_span completes; it must not be cleared in the same onEvaluation callback as the user event. Encapsulate correlation finalization in ChatEvaluationJournal so non-span events do not clear pending/binding state, while a matching host_turn_span clears the pending one-shot and consumes a matching explicit binding. Update electron/main.js to use that lifecycle helper. Add focused regression proving user/assistant events preserve pending state and the final span clears pending + consumes binding. Preserve exact trace/turn/run/wave matching, binding TTL, content-free telemetry, and existing fail-closed behavior.
- Mode: `mcp_only`
- Base HEAD: `0f4e57057d7e6915945070c2e74c786b7ed97f32`
- Worktree fingerprint: `adbcb5c7aab37ca7a6d6b696d15c16711d6ef3e4faf86296ca86417b2f3238fc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12022 | 2026-08-17T07:30:39.446Z | run_started |  | PREFLIGHT |  |
| 12023 | 2026-08-17T07:30:39.887Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12024 | 2026-08-17T07:30:40.027Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12025 | 2026-08-17T07:30:40.166Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12026 | 2026-08-17T07:30:40.314Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 12027 | 2026-08-17T07:30:40.503Z | state_transition | READY | ROUTED | reason=route_selected |
| 12028 | 2026-08-17T07:30:40.938Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2993210f24164e12b74ec2552b8b261c |
| 12029 | 2026-08-17T07:30:41.112Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12030 | 2026-08-17T07:30:41.614Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2993210f24164e12b74ec2552b8b261c |
| 12031 | 2026-08-17T07:30:41.767Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12032 | 2026-08-17T07:30:42.125Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9a07c7c0d6d3d499; input_fingerprint=8dd71493372ddd35f3a88c35e7cd63420e947c4a0bc7617d4c1d9b1f7e58c270 |
| 12033 | 2026-08-17T07:30:42.421Z | managed_process_admitted |  |  | owner=default |
| 12034 | 2026-08-17T07:30:42.686Z | managed_process_started |  |  | owner=default |
| 12035 | 2026-08-17T07:30:43.102Z | managed_process_terminal |  |  | owner=default |
| 12036 | 2026-08-17T07:30:43.387Z | proof_recorded |  |  | stage_id=check:9a07c7c0d6d3d499; status=passed; cache_hit=False; input_fingerprint=8dd71493372ddd35f3a88c35e7cd63420e947c4a0bc7617d4c1d9b1f7e58c270 |
| 12037 | 2026-08-17T07:30:43.541Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:0cfc52e6cfded4a5; input_fingerprint=8b5858e8cfb5faafb6e7adf302539245b14e69d7e19e81607d959153c62fee0e |
| 12038 | 2026-08-17T07:30:43.840Z | managed_process_admitted |  |  | owner=default |
| 12039 | 2026-08-17T07:30:44.087Z | managed_process_started |  |  | owner=default |
| 12040 | 2026-08-17T07:30:44.512Z | managed_process_terminal |  |  | owner=default |
| 12041 | 2026-08-17T07:30:44.827Z | proof_recorded |  |  | stage_id=check:0cfc52e6cfded4a5; status=passed; cache_hit=False; input_fingerprint=8b5858e8cfb5faafb6e7adf302539245b14e69d7e19e81607d959153c62fee0e |
| 12042 | 2026-08-17T07:30:44.998Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1fb9970002b47283; input_fingerprint=90d4afafd2fafb4e56f9fa4c160816f71f9af17cc37efaa3cdc8ae87cb1c075f |
| 12043 | 2026-08-17T07:30:45.304Z | managed_process_admitted |  |  | owner=default |
| 12044 | 2026-08-17T07:30:45.534Z | managed_process_started |  |  | owner=default |
| 12045 | 2026-08-17T07:30:45.929Z | managed_process_terminal |  |  | owner=default |
| 12046 | 2026-08-17T07:30:46.174Z | proof_recorded |  |  | stage_id=check:1fb9970002b47283; status=passed; cache_hit=False; input_fingerprint=90d4afafd2fafb4e56f9fa4c160816f71f9af17cc37efaa3cdc8ae87cb1c075f |
| 12047 | 2026-08-17T07:30:46.324Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1c67f8ed0c89da45; input_fingerprint=29a5260b272f9b5d62a75c0922d835818d584d2375439cc64b6ac3225f57e580 |
| 12048 | 2026-08-17T07:30:46.608Z | managed_process_admitted |  |  | owner=default |
| 12049 | 2026-08-17T07:30:46.843Z | managed_process_started |  |  | owner=default |
| 12050 | 2026-08-17T07:30:47.269Z | managed_process_terminal |  |  | owner=default |
| 12051 | 2026-08-17T07:30:47.557Z | proof_recorded |  |  | stage_id=check:1c67f8ed0c89da45; status=passed; cache_hit=False; input_fingerprint=29a5260b272f9b5d62a75c0922d835818d584d2375439cc64b6ac3225f57e580 |
| 12052 | 2026-08-17T07:30:48.049Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12053 | 2026-08-17T07:31:00.263Z | managed_process_admitted |  |  | owner=default |
| 12054 | 2026-08-17T07:31:00.522Z | managed_process_started |  |  | owner=default |
| 12055 | 2026-08-17T07:31:22.912Z | managed_process_terminal |  |  | owner=default |
| 12056 | 2026-08-17T07:31:33.055Z | managed_process_admitted |  |  | owner=default |
| 12057 | 2026-08-17T07:31:33.356Z | managed_process_started |  |  | owner=default |
| 12058 | 2026-08-17T07:31:36.564Z | managed_process_terminal |  |  | owner=default |
| 12059 | 2026-08-17T07:31:48.312Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12060 | 2026-08-17T07:31:48.670Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9a07c7c0d6d3d499 | passed | 8dd71493372ddd35f3a88c35e7cd63420e947c4a0bc7617d4c1d9b1f7e58c270 | False | 1001 | 0 |
| check:0cfc52e6cfded4a5 | passed | 8b5858e8cfb5faafb6e7adf302539245b14e69d7e19e81607d959153c62fee0e | False | 969 | 0 |
| check:1fb9970002b47283 | passed | 90d4afafd2fafb4e56f9fa4c160816f71f9af17cc37efaa3cdc8ae87cb1c075f | False | 894 | 0 |
| check:1c67f8ed0c89da45 | passed | 29a5260b272f9b5d62a75c0922d835818d584d2375439cc64b6ac3225f57e580 | False | 918 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d0508cf4de09439aa94902f699cd8bd0 | accepted | 0f4e57057d7e6915945070c2e74c786b7ed97f32 | bde0fad9a747b999cc91732d2a51c5ace522e3684c36156504c9b9e96f6d8166 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `39`
- Chain head: `07b9ca7f13657ffb42848c4e8b3683fcca5f13bc6ece25383f0822556a7cd66c`
