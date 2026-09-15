# Orchestration Wave 1

- Run: `d01a5dce50c846fc8e13673cdfc8b3b3`
- Wave: `2f7fed7000b0427ba2a4ab6d08f062ac`
- Objective: C01 packaged cold-start post-canary proof for Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Prove that the accepted canary targeting development Recovery Host PID 47904 / instance 7fbed2a56114c6fa173915c12b6e2b5a completed successfully, and that the already-installed packaged Recovery Supervisor cold-started a new healthy packaged Recovery Host without manual reopen. Require canary LastTaskResult=0; manifest mode=packaged with exact host root/executable and installed supervisor SHA 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab; supervisor healthy/live with zero consecutive failures and no error; Recovery Host PID/instance differ from the killed target; runtime_mode=packaged; process executable is E:\WebMcpAcceptanceHost-1.0.0\Coding Tools MCP.exe with SHA cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c; supervisor last_spawned_pid equals the new Recovery Host PID; canonical supervisor task is Ready or Running. No source edit, process kill, reinstall, restart, reboot, commit, push, release, publish or deploy.
- Objective revision: `1`
- Objective SHA-256: `681c03c3b73567b323ff332337cc677ec65b60331e7beb76364daafc8d786ad2`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `cffd2acee24a4f38f4a83ddfea4c40f766de7a63`
- Worktree fingerprint: `bb9e677899ab7d59711383e7d9f85de6923e6636949b4daae3aaa2fbcdd51f52`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59727 | 2026-09-15T11:31:45.673Z | run_started |  | PREFLIGHT |  |
| 59728 | 2026-09-15T11:31:46.446Z | observation_span_recorded |  |  |  |
| 59729 | 2026-09-15T11:31:47.455Z | observation_span_recorded |  |  |  |
| 59730 | 2026-09-15T11:31:47.664Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59731 | 2026-09-15T11:31:47.855Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59732 | 2026-09-15T11:31:48.071Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59733 | 2026-09-15T11:31:48.262Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59734 | 2026-09-15T11:31:48.536Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59735 | 2026-09-15T11:31:48.715Z | state_transition | READY | ROUTED | reason=route_selected |
| 59736 | 2026-09-15T11:31:48.952Z | observation_span_recorded |  |  |  |
| 59737 | 2026-09-15T11:31:49.936Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bbb2e2e4cbaf4198ba31ff925ca2bc96 |
| 59738 | 2026-09-15T11:31:50.201Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59739 | 2026-09-15T11:31:51.204Z | observation_span_recorded |  |  |  |
| 59740 | 2026-09-15T11:31:51.539Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bbb2e2e4cbaf4198ba31ff925ca2bc96 |
| 59741 | 2026-09-15T11:31:51.733Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59742 | 2026-09-15T11:31:52.632Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7c54c322ac247050; input_fingerprint=9ebb8922c2b811a57f20ca521616423581a6b1741d5dd7497540f4952b20fdfe |
| 59743 | 2026-09-15T11:31:53.001Z | managed_process_admitted |  |  | owner=default |
| 59744 | 2026-09-15T11:31:53.401Z | managed_process_started |  |  | owner=default |
| 59745 | 2026-09-15T11:31:56.684Z | managed_process_terminal |  |  | owner=default |
| 59746 | 2026-09-15T11:31:57.161Z | proof_recorded |  |  | stage_id=check:7c54c322ac247050; status=passed; cache_hit=False; input_fingerprint=9ebb8922c2b811a57f20ca521616423581a6b1741d5dd7497540f4952b20fdfe |
| 59747 | 2026-09-15T11:31:57.365Z | observation_span_recorded |  |  |  |
| 59748 | 2026-09-15T11:31:57.674Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 59749 | 2026-09-15T11:31:57.869Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 59750 | 2026-09-15T11:32:15.522Z | quality_outcome_recorded |  |  |  |
| 59751 | 2026-09-15T11:32:15.732Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 59752 | 2026-09-15T11:32:16.108Z | observation_span_recorded |  |  |  |
| 59753 | 2026-09-15T11:32:16.388Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 59754 | 2026-09-15T11:32:16.583Z | observation_span_recorded |  |  |  |
| 59755 | 2026-09-15T11:32:16.856Z | observation_span_recorded |  |  |  |
| 59756 | 2026-09-15T11:32:17.070Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7c54c322ac247050 | passed | 9ebb8922c2b811a57f20ca521616423581a6b1741d5dd7497540f4952b20fdfe | False | 4070 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6fb3de41a26349f5995a6a2bd92d82f2 | accepted | cffd2acee24a4f38f4a83ddfea4c40f766de7a63 | d40ed776c7dd2cd0b03f766cbbd77e571422e35aca5212dac041ddc9fdd890b4 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `37d9c21464627a9c96d4e8986e92b7ab917c28277a6be5995fdc227998e2fc8d`
