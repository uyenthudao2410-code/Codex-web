# Orchestration Wave 1

- Run: `1d034de5c90d4fe8877f1120b8b3a568`
- Wave: `8f632b5c5e48446b9d5502830bf875a5`
- Objective: Run the full Coding MCP regression suite on the newly accepted cross-session provenance-isolation source, then verify git diff hygiene. This is a proof-only wave: no source mutation, no restart, no commit/push/deploy/publish/release/tag, and no provider/model dispatch.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25968 | 2026-08-21T04:37:58.435Z | run_started |  | PREFLIGHT |  |
| 25969 | 2026-08-21T04:37:59.852Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25970 | 2026-08-21T04:38:02.563Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25971 | 2026-08-21T04:38:03.741Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25972 | 2026-08-21T04:38:04.728Z | state_transition | READY | ROUTED | reason=route_selected |
| 25973 | 2026-08-21T04:38:05.410Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c246e17a9817425f844cfee301bf63d2 |
| 25974 | 2026-08-21T04:38:05.611Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25975 | 2026-08-21T04:38:06.161Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c246e17a9817425f844cfee301bf63d2 |
| 25976 | 2026-08-21T04:38:06.369Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25977 | 2026-08-21T04:38:06.756Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:60a11fb0bb201c3b; input_fingerprint=235d9c99398e036be01005a5ea9d8c311430bfcfd2685af5f8faaf723c59da5a |
| 25978 | 2026-08-21T04:38:07.078Z | managed_process_admitted |  |  | owner=default |
| 25979 | 2026-08-21T04:38:07.485Z | managed_process_started |  |  | owner=default |
| 25980 | 2026-08-21T04:41:18.624Z | managed_process_terminal |  |  | owner=default |
| 25981 | 2026-08-21T04:41:19.099Z | proof_recorded |  |  | stage_id=check:60a11fb0bb201c3b; status=passed; cache_hit=False; input_fingerprint=235d9c99398e036be01005a5ea9d8c311430bfcfd2685af5f8faaf723c59da5a |
| 25982 | 2026-08-21T04:41:19.377Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=9c66595874063d2b40cfb833cd9916cc22e78c0e1e967021707f1778f923a96b |
| 25983 | 2026-08-21T04:41:19.833Z | managed_process_admitted |  |  | owner=default |
| 25984 | 2026-08-21T04:41:20.253Z | managed_process_started |  |  | owner=default |
| 25985 | 2026-08-21T04:41:21.632Z | managed_process_terminal |  |  | owner=default |
| 25986 | 2026-08-21T04:41:21.990Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=9c66595874063d2b40cfb833cd9916cc22e78c0e1e967021707f1778f923a96b |
| 25987 | 2026-08-21T04:41:22.150Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 25988 | 2026-08-21T04:41:39.151Z | quality_outcome_recorded |  |  |  |
| 25989 | 2026-08-21T04:41:39.406Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 25990 | 2026-08-21T04:41:39.731Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:60a11fb0bb201c3b | passed | 235d9c99398e036be01005a5ea9d8c311430bfcfd2685af5f8faaf723c59da5a | False | 191924 | 0 |
| check:466c2f308b48c766 | passed | 9c66595874063d2b40cfb833cd9916cc22e78c0e1e967021707f1778f923a96b | False | 2213 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 86844cbb550f452a925143939c078cfe | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 24751771c3456407d5507b6e66ad70eb8a16d15760dd144357a9d0316d445dfd | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `21ab7e59ff6cd6f1347f978058fdafe8b482138746b074b3a0b3c1f905e6e2d1`
