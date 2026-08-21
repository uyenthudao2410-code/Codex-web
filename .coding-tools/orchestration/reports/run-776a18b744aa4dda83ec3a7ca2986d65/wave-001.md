# Orchestration Wave 1

- Run: `776a18b744aa4dda83ec3a7ca2986d65`
- Wave: `6cc62eff8184430a924d4543acbe48b2`
- Objective: Produce and verify the fresh final local NSIS artifact from the accepted provenance-isolation source fingerprint. Run npm dist (including its full Node/Electron tests), then packaged Recovery smoke, git diff hygiene, source-root cleanliness, and native Windows installer SHA-256/metadata commands. This is local verification only. Do not restart the resident runtime, do not commit/push, do not deploy/publish/release/tag, and do not dispatch any provider/model.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25991 | 2026-08-21T04:42:06.316Z | run_started |  | PREFLIGHT |  |
| 25992 | 2026-08-21T04:42:06.775Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25993 | 2026-08-21T04:42:06.906Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25994 | 2026-08-21T04:42:07.121Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25995 | 2026-08-21T04:42:07.270Z | state_transition | READY | ROUTED | reason=route_selected |
| 25996 | 2026-08-21T04:42:07.859Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3070afe9c5e8415e94fb26e2a7949034 |
| 25997 | 2026-08-21T04:42:07.970Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25998 | 2026-08-21T04:42:08.450Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3070afe9c5e8415e94fb26e2a7949034 |
| 25999 | 2026-08-21T04:42:08.620Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26000 | 2026-08-21T04:42:09.123Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:e449d13f93c687d1; input_fingerprint=df9271b2569d25519bdc317811192c897ebb37ed3ec86e9b66d56e39bdf335ab |
| 26001 | 2026-08-21T04:42:09.538Z | managed_process_admitted |  |  | owner=default |
| 26002 | 2026-08-21T04:42:09.814Z | managed_process_started |  |  | owner=default |
| 26003 | 2026-08-21T04:43:29.883Z | managed_process_admitted |  |  | owner=default |
| 26004 | 2026-08-21T04:43:30.158Z | managed_process_started |  |  | owner=default |
| 26005 | 2026-08-21T04:43:34.183Z | managed_process_terminal |  |  | owner=default |
| 26006 | 2026-08-21T04:43:57.295Z | managed_process_terminal |  |  | owner=default |
| 26007 | 2026-08-21T04:43:57.728Z | proof_recorded |  |  | stage_id=check:e449d13f93c687d1; status=passed; cache_hit=False; input_fingerprint=df9271b2569d25519bdc317811192c897ebb37ed3ec86e9b66d56e39bdf335ab |
| 26008 | 2026-08-21T04:43:57.979Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:470e7e0d382448b5; input_fingerprint=c70ad1b2593bb0cdad62112a06bc26670496911f3fec94175d4d6af8ef1bdbdf |
| 26009 | 2026-08-21T04:43:58.436Z | managed_process_admitted |  |  | owner=default |
| 26010 | 2026-08-21T04:43:58.853Z | managed_process_started |  |  | owner=default |
| 26011 | 2026-08-21T04:44:07.421Z | managed_process_terminal |  |  | owner=default |
| 26012 | 2026-08-21T04:44:07.756Z | proof_recorded |  |  | stage_id=check:470e7e0d382448b5; status=passed; cache_hit=False; input_fingerprint=c70ad1b2593bb0cdad62112a06bc26670496911f3fec94175d4d6af8ef1bdbdf |
| 26013 | 2026-08-21T04:44:07.955Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=a435abe502c5800aaa850acbc67e95078d657196d4f78c6a4d6dcce3d69f7096 |
| 26014 | 2026-08-21T04:44:08.401Z | managed_process_admitted |  |  | owner=default |
| 26015 | 2026-08-21T04:44:08.688Z | managed_process_started |  |  | owner=default |
| 26016 | 2026-08-21T04:44:10.219Z | managed_process_terminal |  |  | owner=default |
| 26017 | 2026-08-21T04:44:10.753Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=a435abe502c5800aaa850acbc67e95078d657196d4f78c6a4d6dcce3d69f7096 |
| 26018 | 2026-08-21T04:44:11.024Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:5d2bd3e0ac5171d0; input_fingerprint=af9c40bd71bd297ba022b8199cf3d04dbfaa50b40a3cebadad0358b503f40e5e |
| 26019 | 2026-08-21T04:44:11.458Z | managed_process_admitted |  |  | owner=default |
| 26020 | 2026-08-21T04:44:11.835Z | managed_process_started |  |  | owner=default |
| 26021 | 2026-08-21T04:44:12.316Z | managed_process_terminal |  |  | owner=default |
| 26022 | 2026-08-21T04:44:12.618Z | proof_recorded |  |  | stage_id=check:5d2bd3e0ac5171d0; status=passed; cache_hit=False; input_fingerprint=af9c40bd71bd297ba022b8199cf3d04dbfaa50b40a3cebadad0358b503f40e5e |
| 26023 | 2026-08-21T04:44:12.785Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7fa1fd68baed8583; input_fingerprint=3f8b2ef7c64bddb28c9794d237952ff60f12d03c07b4df1763f60b723feadf7c |
| 26024 | 2026-08-21T04:44:13.218Z | managed_process_admitted |  |  | owner=default |
| 26025 | 2026-08-21T04:44:13.579Z | managed_process_started |  |  | owner=default |
| 26026 | 2026-08-21T04:44:13.993Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 26027 | 2026-08-21T04:44:14.391Z | proof_recorded |  |  | stage_id=check:7fa1fd68baed8583; status=passed; cache_hit=False; input_fingerprint=3f8b2ef7c64bddb28c9794d237952ff60f12d03c07b4df1763f60b723feadf7c |
| 26028 | 2026-08-21T04:44:14.578Z | proof_cache_miss |  |  | reason=cold; stage_id=check:37ac463eac3b5626; input_fingerprint=f8e8eb35ffba2938ea324875869591275ba155d4b801ffce185b7f77d5852db9 |
| 26029 | 2026-08-21T04:44:14.940Z | managed_process_admitted |  |  | owner=default |
| 26030 | 2026-08-21T04:44:15.284Z | managed_process_started |  |  | owner=default |
| 26031 | 2026-08-21T04:44:15.658Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 26032 | 2026-08-21T04:44:15.978Z | proof_recorded |  |  | stage_id=check:37ac463eac3b5626; status=passed; cache_hit=False; input_fingerprint=f8e8eb35ffba2938ea324875869591275ba155d4b801ffce185b7f77d5852db9 |
| 26033 | 2026-08-21T04:44:16.239Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26034 | 2026-08-21T04:44:43.986Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject this final package proof wave for provenance integrity only. All six requested checks passed on source fingerprint 48bed1f1ea0ed7f3776542f9981413b9a2b9aa4646462bbac6665351d990941e, including npm dist, packaged Recovery smoke, diff/source-root hygiene, installer SHA-256 and metadata. However, the resident MCP runtime is still running pre-fix code and auto-bound an unrelated attendance-timesheet-crawler gh workflow command into this exact run/wave. The source fix is already accepted and full MCP 493/3 is green, but this contaminated live proof wave must not be accepted. Preserve the generated artifact; next strategy is a short independent artifact re-proof and explicit classification that resident runtime activation requires restart.; failure_class=SOL_REJECTED |
| 26035 | 2026-08-21T04:44:44.168Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 26036 | 2026-08-21T04:44:44.370Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e449d13f93c687d1 | passed | df9271b2569d25519bdc317811192c897ebb37ed3ec86e9b66d56e39bdf335ab | False | 108253 | 0 |
| check:470e7e0d382448b5 | passed | c70ad1b2593bb0cdad62112a06bc26670496911f3fec94175d4d6af8ef1bdbdf | False | 9403 | 0 |
| check:466c2f308b48c766 | passed | a435abe502c5800aaa850acbc67e95078d657196d4f78c6a4d6dcce3d69f7096 | False | 2229 | 0 |
| check:5d2bd3e0ac5171d0 | passed | af9c40bd71bd297ba022b8199cf3d04dbfaa50b40a3cebadad0358b503f40e5e | False | 1315 | 0 |
| check:7fa1fd68baed8583 | passed | 3f8b2ef7c64bddb28c9794d237952ff60f12d03c07b4df1763f60b723feadf7c | False | 1028 | 0 |
| check:37ac463eac3b5626 | passed | f8e8eb35ffba2938ea324875869591275ba155d4b801ffce185b7f77d5852db9 | False | 913 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `89`
- Chain head: `b99c477b47e14e2ec49142a681bedd518b147b56cc1d26daccf84dbe6acdfab3`
