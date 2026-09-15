# Orchestration Wave 2

- Run: `b194ab1e311e42efa1dd0614ca245037`
- Wave: `09a6713523104d3b8057cf36b23e6fdf`
- Objective: Arm durable pre-reboot evidence for C01/M02 machine-A Restart sample 1 under Problem prl-22e670302757c9b7663170e226ed7c26 revision 1, using accepted packaged cold-start checkpoint 6fb3de41a26349f5995a6a2bd92d82f2. Record a privacy-safe receipt at .coding-tools/reboot-acceptance/c01-m02-machine-a-restart-1-pre.json with UTC capture time, Windows LastBootUpTime, exact packaged manifest/root/executable identities, installed executable and supervisor script SHA-256, live supervisor and packaged Recovery Host PID/instance, zero-failure status, Scheduled Task action/state plus boolean same-user principal match computed by normalized SID equality and trigger class names, and expected post-reboot assertions. Store no username, SID, token, credential, raw descriptor, or PII. Verify receipt parsing and exact identities, then unregister only the completed one-shot canary task when its LastTaskResult=0. Do not reboot yet, edit source, reinstall, commit, push, release, publish or deploy.
- Objective revision: `2`
- Objective SHA-256: `c9212d9102974c84f8c36bca5c93ca62c27a2657cd320a725a3f3e24802eeaae`
- Objective source: `replan_request`
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
| 59784 | 2026-09-15T11:34:48.844Z | wave_replanned |  | PREFLIGHT | reason=The prior wave reached exact packaged hash/health gates but exit 32 because it compared Scheduled Task Principal.UserId and current Windows identity as raw strings. Earlier accepted launch-ladder evidence established that representation may differ while normalized SID is the same account. Change only this oracle to normalized SID equality without storing the SID or username; all product state and artifact assertions remain unchanged. |
| 59785 | 2026-09-15T11:34:49.319Z | observation_span_recorded |  |  |  |
| 59786 | 2026-09-15T11:34:50.506Z | observation_span_recorded |  |  |  |
| 59787 | 2026-09-15T11:34:50.743Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59788 | 2026-09-15T11:34:50.970Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59789 | 2026-09-15T11:34:51.186Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59790 | 2026-09-15T11:34:51.395Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59791 | 2026-09-15T11:34:51.595Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59792 | 2026-09-15T11:34:51.771Z | state_transition | READY | ROUTED | reason=route_selected |
| 59793 | 2026-09-15T11:34:52.183Z | observation_span_recorded |  |  |  |
| 59794 | 2026-09-15T11:34:53.195Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=23c5e7bb33194a389e28549e79285122 |
| 59795 | 2026-09-15T11:34:53.372Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59796 | 2026-09-15T11:34:54.352Z | observation_span_recorded |  |  |  |
| 59797 | 2026-09-15T11:34:54.767Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=23c5e7bb33194a389e28549e79285122 |
| 59798 | 2026-09-15T11:34:54.956Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59799 | 2026-09-15T11:34:55.885Z | proof_cache_miss |  |  | reason=cold; stage_id=check:639ea42203168afb; input_fingerprint=f55206249bba5e6bfdf3a5c80f86a67062d604d85b49f39686e1e9f14e46d0f4 |
| 59800 | 2026-09-15T11:34:56.338Z | managed_process_admitted |  |  | owner=default |
| 59801 | 2026-09-15T11:34:56.724Z | managed_process_started |  |  | owner=default |
| 59802 | 2026-09-15T11:34:59.380Z | managed_process_terminal |  |  | owner=default |
| 59803 | 2026-09-15T11:34:59.886Z | proof_recorded |  |  | stage_id=check:639ea42203168afb; status=passed; cache_hit=False; input_fingerprint=f55206249bba5e6bfdf3a5c80f86a67062d604d85b49f39686e1e9f14e46d0f4 |
| 59804 | 2026-09-15T11:35:00.124Z | proof_cache_miss |  |  | reason=cold; stage_id=check:eefef2d0f6511903; input_fingerprint=4bad8917e229889786a0a4057ff4ad699a044141aedc27e94f55c19d09513558 |
| 59805 | 2026-09-15T11:35:00.555Z | managed_process_admitted |  |  | owner=default |
| 59806 | 2026-09-15T11:35:00.965Z | managed_process_started |  |  | owner=default |
| 59807 | 2026-09-15T11:35:02.780Z | managed_process_terminal |  |  | owner=default |
| 59808 | 2026-09-15T11:35:03.248Z | proof_recorded |  |  | stage_id=check:eefef2d0f6511903; status=passed; cache_hit=False; input_fingerprint=4bad8917e229889786a0a4057ff4ad699a044141aedc27e94f55c19d09513558 |
| 59809 | 2026-09-15T11:35:03.460Z | observation_span_recorded |  |  |  |
| 59810 | 2026-09-15T11:35:03.754Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 59811 | 2026-09-15T11:35:04.073Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 59814 | 2026-09-15T11:36:06.584Z | quality_outcome_recorded |  |  |  |
| 59815 | 2026-09-15T11:36:06.770Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 59816 | 2026-09-15T11:36:07.059Z | observation_span_recorded |  |  |  |
| 59817 | 2026-09-15T11:36:07.276Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 59818 | 2026-09-15T11:36:07.463Z | observation_span_recorded |  |  |  |
| 59819 | 2026-09-15T11:36:07.746Z | observation_span_recorded |  |  |  |
| 59820 | 2026-09-15T11:36:08.000Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:639ea42203168afb | passed | f55206249bba5e6bfdf3a5c80f86a67062d604d85b49f39686e1e9f14e46d0f4 | False | 3555 | 0 |
| check:eefef2d0f6511903 | passed | 4bad8917e229889786a0a4057ff4ad699a044141aedc27e94f55c19d09513558 | False | 2665 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c8f32a66c7714204bcdd64162dc20ee1 | accepted | cffd2acee24a4f38f4a83ddfea4c40f766de7a63 | 04d9f19cb0112e060c88cc025a61110cdc7fca49144492e14b49f231776cd28c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `ebaf7354400066ee3ea7815d2f1ccb51a16da0f36c69239a967c75fd4f1b6011`
