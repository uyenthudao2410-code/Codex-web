# Orchestration Wave 2

- Run: `ee62554e999645169a35f64864c8dbf0`
- Wave: `7ac786f081e54a36b9c6ce57f337d313`
- Objective: Apply the smallest lifecycle fix for the active mcp_only RUN/WAVE: AcceptedCodeActivationController must not start while a durable full-clean epoch is VERIFYING/FAILED/expired or READY-but-blocked, but RecoveryHost supervision must idempotently arm it as soon as the same durable epoch becomes READY with admission OPEN after bootstrap/finalize. Preserve bootstrap and ready-adoption authority guards. Do not create connector/discovery receipts, use raw HTTP/direct SQLite/force release, restart runtime, commit, push, deploy, or broaden scope.
- Objective revision: `1`
- Objective SHA-256: `55faf10dc33e889f9941d148abf0ec2ecdc3284960b8912b7528022050f1a15b`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a357e1bb45a68cfaf25b8a2aa99a133ab256102c`
- Worktree fingerprint: `437b65c6056a12556e495ef4db490469019bf685cbdd32f349d2cb7fc1dee682`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32850 | 2026-08-30T20:18:05.506Z | wave_replanned |  | PREFLIGHT | reason=Focused proof reached the new lifecycle assertions successfully and failed only during teardown of the newly added fixture: RecoveryHost.stop() correctly calls gateway.stop(), while this fixture supplied gateway={}. Changed strategy is fixture-only: add the missing no-op stop method and rerun the exact requested proof without altering production logic. |
| 32851 | 2026-08-30T20:18:05.780Z | observation_span_recorded |  |  |  |
| 32852 | 2026-08-30T20:18:06.000Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32853 | 2026-08-30T20:18:06.241Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32854 | 2026-08-30T20:18:06.479Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 32855 | 2026-08-30T20:18:06.682Z | state_transition | READY | ROUTED | reason=route_selected |
| 32856 | 2026-08-30T20:18:06.909Z | observation_span_recorded |  |  |  |
| 32857 | 2026-08-30T20:18:07.725Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c50e4c268b154731bbe677cf9f577503 |
| 32858 | 2026-08-30T20:18:07.951Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32859 | 2026-08-30T20:18:08.733Z | patch_surface_observed |  |  |  |
| 32860 | 2026-08-30T20:18:08.905Z | observation_span_recorded |  |  |  |
| 32861 | 2026-08-30T20:18:09.265Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c50e4c268b154731bbe677cf9f577503 |
| 32862 | 2026-08-30T20:18:09.427Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32863 | 2026-08-30T20:18:10.132Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=dbb02920642fff09908e58f0d818d988e848a9eadf994e9cf4640be69f54b251 |
| 32864 | 2026-08-30T20:18:10.492Z | managed_process_admitted |  |  | owner=default |
| 32865 | 2026-08-30T20:18:10.851Z | managed_process_started |  |  | owner=default |
| 32866 | 2026-08-30T20:18:44.007Z | managed_process_terminal |  |  | owner=default |
| 32867 | 2026-08-30T20:18:45.132Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=dbb02920642fff09908e58f0d818d988e848a9eadf994e9cf4640be69f54b251 |
| 32868 | 2026-08-30T20:18:46.051Z | observation_span_recorded |  |  |  |
| 32869 | 2026-08-30T20:18:46.249Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 32870 | 2026-08-30T22:38:17.252Z | managed_process_admitted |  |  | owner=default |
| 32871 | 2026-08-30T22:38:17.588Z | managed_process_started |  |  | owner=default |
| 32872 | 2026-08-30T22:38:52.787Z | managed_process_terminal |  |  | owner=default |
| 32873 | 2026-08-30T23:40:24.225Z | observation_span_recorded |  |  |  |
| 32874 | 2026-08-30T23:40:24.414Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject exact wave because wave-2 write lease allowed only tests/recovery-host.test.js; the observed file in that lease was pre-existing dirty, while electron/services/recoveryHost.js production source from wave-1 was not durably adopted into this wave. Replan on the same RUN with an exact two-file lease and exact-byte existing-file adoption before acceptance.; failure_class=SOL_REJECTED |
| 32875 | 2026-08-30T23:40:24.618Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 32876 | 2026-08-30T23:40:24.867Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | dbb02920642fff09908e58f0d818d988e848a9eadf994e9cf4640be69f54b251 | False | 34593 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `96`
- Chain head: `bc31868acd8777955479f2e126e7679db7e39db2513ec563fcbd58423293e6fb`
