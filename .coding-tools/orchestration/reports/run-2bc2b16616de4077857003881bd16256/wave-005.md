# Orchestration Wave 5

- Run: `2bc2b16616de4077857003881bd16256`
- Wave: `870b8f57db2345ae959422d568998d43`
- Objective: Diagnose the current packaged Recovery Supervisor Install failure for C01/M02 on Machine A without leaving packaged state behind. The previous Install reached the official installed supervisor script, returned exit 1 after about 26 seconds, and the wrapper successfully restored development/healthy state. Current rollback state is supervisor development/healthy PID 43300 and Recovery Host PID 19280 instance 5d13d8ac21067c251d8179f880629b1a. Re-run the exact packaged Install only to capture its official JSON output and a safe non-secret transitional snapshot before rollback: manifest mode/hash, supervisor state/pid/last_check/last_error/capability/manifest_sha/last_host/last_spawned, Scheduled Task state/last result/action. Never expose recovery descriptor token. Always restore development supervisor afterward whether Install succeeds or fails, and verify rollback health plus unchanged Recovery Host identity. Do not reboot/logoff/restart runtime, edit source, commit, push, release, publish, or deploy.
- Objective revision: `5`
- Objective SHA-256: `da63505e8814db3b0e107e5596a4bd5f80b4c507cf828a8eca402b7412a8fa9c`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `0a67c9f11d3619d4449f50f6f4c548dad41cab5dab6e68071cefa8baca9239fa`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58880 | 2026-09-15T09:19:46.492Z | wave_replanned |  | PREFLIGHT | reason=After acknowledging wave e0a22fe1bcee4eb0b7d29c851d0ea38e, task_control reconciliation now proves active_claim_count=0, active_command_count=0 and quiescent=true. The failed Install's official JSON was swallowed by the prior wrapper. Historical Get-OptionalProperty suspicion was later falsified against exact source, so the changed strategy is to capture current official Install output plus safe transitional manifest/status/task fields before guaranteed development rollback. |
| 58881 | 2026-09-15T09:19:47.082Z | observation_span_recorded |  |  |  |
| 58882 | 2026-09-15T09:19:53.278Z | observation_span_recorded |  |  |  |
| 58883 | 2026-09-15T09:19:53.612Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58914 | 2026-09-15T09:37:18.995Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58915 | 2026-09-15T09:37:19.449Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58916 | 2026-09-15T09:37:19.779Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58917 | 2026-09-15T09:37:20.076Z | state_transition | READY | ROUTED | reason=route_selected |
| 58918 | 2026-09-15T09:37:20.423Z | observation_span_recorded |  |  |  |
| 58919 | 2026-09-15T09:37:21.294Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2b522c669ee24dc5ac60dc2b9f524aef |
| 58920 | 2026-09-15T09:37:21.800Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58921 | 2026-09-15T09:37:22.547Z | observation_span_recorded |  |  |  |
| 58922 | 2026-09-15T09:37:23.134Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2b522c669ee24dc5ac60dc2b9f524aef |
| 58923 | 2026-09-15T09:37:23.451Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58924 | 2026-09-15T09:37:24.085Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cf7f79ca69217ce2; input_fingerprint=3685b7aed1941bfcaf72785e793f69dbe6c281afb4cc31ec02c20064b25f9009 |
| 58925 | 2026-09-15T09:37:24.672Z | managed_process_admitted |  |  | owner=default |
| 58926 | 2026-09-15T09:37:25.295Z | managed_process_started |  |  | owner=default |
| 58927 | 2026-09-15T09:37:50.446Z | managed_process_terminal |  |  | owner=default |
| 58928 | 2026-09-15T09:37:51.123Z | proof_recorded |  |  | stage_id=check:cf7f79ca69217ce2; status=passed; cache_hit=False; input_fingerprint=3685b7aed1941bfcaf72785e793f69dbe6c281afb4cc31ec02c20064b25f9009 |
| 58929 | 2026-09-15T09:37:52.298Z | observation_span_recorded |  |  |  |
| 58930 | 2026-09-15T09:37:52.658Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 58931 | 2026-09-15T09:37:52.750Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 58932 | 2026-09-15T09:38:35.848Z | quality_outcome_recorded |  |  |  |
| 58933 | 2026-09-15T09:38:36.279Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 58934 | 2026-09-15T09:38:36.979Z | observation_span_recorded |  |  |  |
| 58935 | 2026-09-15T09:38:37.461Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 58936 | 2026-09-15T09:38:37.892Z | observation_span_recorded |  |  |  |
| 58937 | 2026-09-15T09:38:38.337Z | observation_span_recorded |  |  |  |
| 58938 | 2026-09-15T09:38:38.890Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:cf7f79ca69217ce2 | passed | 3685b7aed1941bfcaf72785e793f69dbe6c281afb4cc31ec02c20064b25f9009 | False | 26478 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6c821be1d56f4db196d8c2f5032c8cfd | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | b3a2b1dc2476668503adce8f62a3b0f2d2951443c712da972da4bc9a6daca409 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `a1b6c357935ccb198a60f090f208d3c0dbec36c62138d7762fa8ed0a545815c5`
