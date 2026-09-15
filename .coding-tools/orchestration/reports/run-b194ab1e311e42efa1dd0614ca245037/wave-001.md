# Orchestration Wave 1

- Run: `b194ab1e311e42efa1dd0614ca245037`
- Wave: `95f130cde253439fb7b40aeeca757ba9`
- Objective: Arm durable pre-reboot evidence for C01/M02 machine-A Restart sample 1 under Problem prl-22e670302757c9b7663170e226ed7c26 revision 1, using accepted packaged cold-start checkpoint 6fb3de41a26349f5995a6a2bd92d82f2. Record a privacy-safe receipt at .coding-tools/reboot-acceptance/c01-m02-machine-a-restart-1-pre.json with UTC capture time, Windows LastBootUpTime, exact packaged manifest/root/executable identities, installed executable and supervisor script SHA-256, live supervisor and packaged Recovery Host PID/instance, zero-failure status, Scheduled Task action/state plus boolean same-user principal match and trigger class names, and the expected post-reboot assertions. Do not store tokens, raw descriptor content, username/SID, credentials, or PII. Require exact executable SHA cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c and supervisor script SHA 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab; manifest/status must be packaged/healthy with live processes and zero failures. Verify the receipt parses and matches live state, then unregister only the completed one-shot canary task if its LastTaskResult is 0. Do not reboot yet, edit source, reinstall, commit, push, release, publish or deploy.
- Objective revision: `1`
- Objective SHA-256: `d5e9de3a799a69d26b0dcd6483cc1463cb61a61e667c521ee76d8e281795b938`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `cffd2acee24a4f38f4a83ddfea4c40f766de7a63`
- Worktree fingerprint: `bb9e677899ab7d59711383e7d9f85de6923e6636949b4daae3aaa2fbcdd51f52`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59759 | 2026-09-15T11:33:43.540Z | run_started |  | PREFLIGHT |  |
| 59760 | 2026-09-15T11:33:44.361Z | observation_span_recorded |  |  |  |
| 59761 | 2026-09-15T11:33:45.545Z | observation_span_recorded |  |  |  |
| 59762 | 2026-09-15T11:33:45.751Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59763 | 2026-09-15T11:33:45.998Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59764 | 2026-09-15T11:33:46.262Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59765 | 2026-09-15T11:33:46.459Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59766 | 2026-09-15T11:33:46.639Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59767 | 2026-09-15T11:33:46.855Z | state_transition | READY | ROUTED | reason=route_selected |
| 59768 | 2026-09-15T11:33:47.137Z | observation_span_recorded |  |  |  |
| 59769 | 2026-09-15T11:33:48.224Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6d7992dd2e764a3aacbb8197e971662e |
| 59770 | 2026-09-15T11:33:48.451Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59771 | 2026-09-15T11:33:49.409Z | observation_span_recorded |  |  |  |
| 59772 | 2026-09-15T11:33:49.760Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6d7992dd2e764a3aacbb8197e971662e |
| 59773 | 2026-09-15T11:33:50.001Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59774 | 2026-09-15T11:33:51.117Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8bd26e2473a2ecb4; input_fingerprint=cd707c61a4dbecf8cffa2fb6a352a7c2ae054e7214f68f7c5cd748fbfb2392aa |
| 59775 | 2026-09-15T11:33:51.624Z | managed_process_admitted |  |  | owner=default |
| 59776 | 2026-09-15T11:33:52.024Z | managed_process_started |  |  | owner=default |
| 59777 | 2026-09-15T11:33:54.601Z | managed_process_terminal |  |  | owner=default |
| 59778 | 2026-09-15T11:33:55.110Z | proof_recorded |  |  | stage_id=check:8bd26e2473a2ecb4; status=failed; cache_hit=False; input_fingerprint=cd707c61a4dbecf8cffa2fb6a352a7c2ae054e7214f68f7c5cd748fbfb2392aa |
| 59779 | 2026-09-15T11:33:55.434Z | observation_span_recorded |  |  |  |
| 59780 | 2026-09-15T11:33:55.754Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 59781 | 2026-09-15T11:33:55.926Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 59782 | 2026-09-15T11:33:56.210Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 59783 | 2026-09-15T11:34:18.239Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8bd26e2473a2ecb4 | failed | cd707c61a4dbecf8cffa2fb6a352a7c2ae054e7214f68f7c5cd748fbfb2392aa | False | 3485 | 32 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `ebaf7354400066ee3ea7815d2f1ccb51a16da0f36c69239a967c75fd4f1b6011`
