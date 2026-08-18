# Orchestration Wave 2

- Run: `bb477fc737fd40038823bd20ecc2cc49`
- Wave: `32196acc7f3b4e31adc7cc330b24dcca`
- Objective: P3 activation preflight only: rebuild exact-HEAD webcodex-server and webcodex-runner, verify both binary versions carry current Git HEAD bc17700e, then run scripts/e2e_server_first_snapshot_ws.ps1 as a real-process loopback SourceSnapshot server-first dispatch/fallback mechanism canary. Do not modify product source, do not create representative evaluation tags, and do not interpret this canary as P3 efficacy evidence.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e8c159440c324c40eb2c8f2f3d85416a377d64be6d5c466ea3d0bd1089609264`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15850 | 2026-08-17T20:34:53.420Z | wave_replanned |  | PREFLIGHT | reason=Previous build command incorrectly addressed webcodex-runner as a bin in the default package. Retained stderr proves it is a separate Cargo package; use package-qualified runner build, keeping source and experiment scope unchanged. |
| 15851 | 2026-08-17T20:34:53.789Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15852 | 2026-08-17T20:34:53.925Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15853 | 2026-08-17T20:34:54.026Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15854 | 2026-08-17T20:34:54.137Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15855 | 2026-08-17T20:34:54.263Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15856 | 2026-08-17T20:34:54.390Z | state_transition | READY | ROUTED | reason=route_selected |
| 15857 | 2026-08-17T20:34:54.755Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cb6481da36eb457b9469818cfe05bc8a |
| 15858 | 2026-08-17T20:34:54.881Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15859 | 2026-08-17T20:34:55.262Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cb6481da36eb457b9469818cfe05bc8a |
| 15860 | 2026-08-17T20:34:55.373Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15861 | 2026-08-17T20:34:55.678Z | proof_cache_miss |  |  | reason=cold; stage_id=check:059f42ba98d05913; input_fingerprint=8e0d9b2de1ed345364abb7274530d344ab46946b120e088e82c433610c4162c3 |
| 15862 | 2026-08-17T20:34:55.956Z | managed_process_admitted |  |  | owner=default |
| 15863 | 2026-08-17T20:34:56.178Z | managed_process_started |  |  | owner=default |
| 15864 | 2026-08-17T20:36:17.526Z | managed_process_terminal |  |  | owner=default |
| 15865 | 2026-08-17T20:36:17.791Z | proof_recorded |  |  | stage_id=check:059f42ba98d05913; status=passed; cache_hit=False; input_fingerprint=8e0d9b2de1ed345364abb7274530d344ab46946b120e088e82c433610c4162c3 |
| 15866 | 2026-08-17T20:36:17.907Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a8873234b9b9325d; input_fingerprint=87d234d20e4791075067153fa9f59cc2b1ef0fd984d143a541fd1adcf1912fa0 |
| 15867 | 2026-08-17T20:36:18.456Z | managed_process_admitted |  |  | owner=default |
| 15868 | 2026-08-17T20:36:18.967Z | managed_process_started |  |  | owner=default |
| 15869 | 2026-08-17T20:36:48.678Z | managed_process_terminal |  |  | owner=default |
| 15870 | 2026-08-17T20:36:48.912Z | proof_recorded |  |  | stage_id=check:a8873234b9b9325d; status=passed; cache_hit=False; input_fingerprint=87d234d20e4791075067153fa9f59cc2b1ef0fd984d143a541fd1adcf1912fa0 |
| 15871 | 2026-08-17T20:36:49.118Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:e778e28faf8d6ce3; input_fingerprint=fc7e39afca67c29e4c5d94e4d9e01a663c50bc6add53c0564993cb060641c594 |
| 15872 | 2026-08-17T20:36:49.371Z | managed_process_admitted |  |  | owner=default |
| 15873 | 2026-08-17T20:36:49.672Z | managed_process_started |  |  | owner=default |
| 15874 | 2026-08-17T20:36:50.455Z | managed_process_terminal |  |  | owner=default |
| 15875 | 2026-08-17T20:36:50.705Z | proof_recorded |  |  | stage_id=check:e778e28faf8d6ce3; status=passed; cache_hit=False; input_fingerprint=fc7e39afca67c29e4c5d94e4d9e01a663c50bc6add53c0564993cb060641c594 |
| 15876 | 2026-08-17T20:36:50.844Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bb2279ca4dd8ce58; input_fingerprint=f751e7b861a4cb0ac939cd8b3e15380ae52d2b704b6c979f14540a24f3d909d6 |
| 15877 | 2026-08-17T20:36:51.526Z | managed_process_admitted |  |  | owner=default |
| 15878 | 2026-08-17T20:36:52.380Z | managed_process_started |  |  | owner=default |
| 15879 | 2026-08-17T20:36:52.808Z | managed_process_terminal |  |  | owner=default |
| 15880 | 2026-08-17T20:36:53.061Z | proof_recorded |  |  | stage_id=check:bb2279ca4dd8ce58; status=passed; cache_hit=False; input_fingerprint=f751e7b861a4cb0ac939cd8b3e15380ae52d2b704b6c979f14540a24f3d909d6 |
| 15881 | 2026-08-17T20:36:53.188Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:726c4ad29a752dad; input_fingerprint=fcfbc9d44787405f73b12af532a27339c8a3d559f50a18330683f15bacbae7b3 |
| 15882 | 2026-08-17T20:36:53.425Z | managed_process_admitted |  |  | owner=default |
| 15883 | 2026-08-17T20:36:53.655Z | managed_process_started |  |  | owner=default |
| 15884 | 2026-08-17T20:38:37.468Z | managed_process_terminal |  |  | owner=default |
| 15885 | 2026-08-17T20:38:37.717Z | proof_recorded |  |  | stage_id=check:726c4ad29a752dad; status=passed; cache_hit=False; input_fingerprint=fcfbc9d44787405f73b12af532a27339c8a3d559f50a18330683f15bacbae7b3 |
| 15886 | 2026-08-17T20:38:37.833Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15887 | 2026-08-17T23:25:17.503Z | managed_process_admitted |  |  | owner=default |
| 15888 | 2026-08-17T23:25:17.732Z | managed_process_started |  |  | owner=default |
| 15889 | 2026-08-17T23:25:18.116Z | managed_process_terminal |  |  | owner=default |
| 15890 | 2026-08-17T23:26:10.931Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15891 | 2026-08-17T23:26:11.214Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:059f42ba98d05913 | passed | 8e0d9b2de1ed345364abb7274530d344ab46946b120e088e82c433610c4162c3 | False | 81864 | 0 |
| check:a8873234b9b9325d | passed | 87d234d20e4791075067153fa9f59cc2b1ef0fd984d143a541fd1adcf1912fa0 | False | 30771 | 0 |
| check:e778e28faf8d6ce3 | passed | fc7e39afca67c29e4c5d94e4d9e01a663c50bc6add53c0564993cb060641c594 | False | 1340 | 0 |
| check:bb2279ca4dd8ce58 | passed | f751e7b861a4cb0ac939cd8b3e15380ae52d2b704b6c979f14540a24f3d909d6 | False | 1868 | 0 |
| check:726c4ad29a752dad | passed | fcfbc9d44787405f73b12af532a27339c8a3d559f50a18330683f15bacbae7b3 | False | 104280 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 95ac76166a794201982f59e3f7b804d0 | accepted | bc17700e475ce74c96a9547117aade58823f0811 | e03f61f91a750786973c00e755d351993f841675f94ea4f980e063c0d3a5465f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `6f11d1d0e8be75c080bd2bba6a64cfe15d85ee89238cf796040bd1c0bf8dcff5`
