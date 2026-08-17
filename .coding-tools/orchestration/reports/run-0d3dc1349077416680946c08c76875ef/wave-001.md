# Orchestration Wave 1

- Run: `0d3dc1349077416680946c08c76875ef`
- Wave: `68c8cab1593f46249c3f801d7e85cdcf`
- Objective: Complete P0.2 coherence using only the product-native authenticated Recovery Host IPC. Instantiate RecoveryIpcClient with createRuntimePaths for the current %APPDATA%\web-mcp-assistant data root; call lightweightSnapshot(), which internally performs authenticated primary Coding MCP health. Output only content-free snapshot fields, never the descriptor token. Require primary mcpRunning/nativeAlive/tunnelRunning/fullyReady all true; require device.coding endpoint_device_instance_id equals current device_instance_id; require device.recovery host/mcp/tunnel all healthy; independently require Recovery MCP /healthz ok with matching device_id/device_instance_id; require exactly one listener each on 18766,18767,18082,18083 with source-tree native-python/tunnel-client executables; inspect tunnel command lines internally and output only boolean endpoint/health-port matches; require Recovery Supervisor healthy/alive and exact Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Also require the failed temporary helper directory/result are absent. No mutation.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12922 | 2026-08-17T08:59:48.111Z | run_started |  | PREFLIGHT |  |
| 12923 | 2026-08-17T08:59:48.553Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12924 | 2026-08-17T08:59:48.701Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12925 | 2026-08-17T08:59:48.912Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12926 | 2026-08-17T08:59:49.112Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12927 | 2026-08-17T08:59:49.262Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12928 | 2026-08-17T08:59:49.510Z | state_transition | READY | ROUTED | reason=route_selected |
| 12929 | 2026-08-17T08:59:49.979Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4ada3e40242040d0b41d7b6ed30f6098 |
| 12930 | 2026-08-17T08:59:50.140Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12931 | 2026-08-17T08:59:50.700Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4ada3e40242040d0b41d7b6ed30f6098 |
| 12932 | 2026-08-17T08:59:50.893Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12933 | 2026-08-17T08:59:51.421Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ede209319129a3c5; input_fingerprint=a91c080c8c7245bf57ccc751fa527a3d9c726ba289da2a2d15198d13ab5b0038 |
| 12934 | 2026-08-17T08:59:51.801Z | managed_process_admitted |  |  | owner=default |
| 12935 | 2026-08-17T08:59:52.270Z | managed_process_started |  |  | owner=default |
| 12936 | 2026-08-17T08:59:52.695Z | managed_process_terminal |  |  | owner=default |
| 12937 | 2026-08-17T08:59:53.070Z | proof_recorded |  |  | stage_id=check:ede209319129a3c5; status=passed; cache_hit=False; input_fingerprint=a91c080c8c7245bf57ccc751fa527a3d9c726ba289da2a2d15198d13ab5b0038 |
| 12938 | 2026-08-17T08:59:53.273Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8efbf980357b794f; input_fingerprint=1bcf1047e7116d23c4f7fa3b6795bd39e2968b18ea59d30fb05cc11e6b83ede4 |
| 12939 | 2026-08-17T08:59:53.611Z | managed_process_admitted |  |  | owner=default |
| 12940 | 2026-08-17T08:59:53.870Z | managed_process_started |  |  | owner=default |
| 12941 | 2026-08-17T08:59:56.245Z | managed_process_terminal |  |  | owner=default |
| 12942 | 2026-08-17T08:59:56.718Z | proof_recorded |  |  | stage_id=check:8efbf980357b794f; status=passed; cache_hit=False; input_fingerprint=1bcf1047e7116d23c4f7fa3b6795bd39e2968b18ea59d30fb05cc11e6b83ede4 |
| 12943 | 2026-08-17T08:59:56.947Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12944 | 2026-08-17T09:00:15.853Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12945 | 2026-08-17T09:00:16.316Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ede209319129a3c5 | passed | a91c080c8c7245bf57ccc751fa527a3d9c726ba289da2a2d15198d13ab5b0038 | False | 1273 | 0 |
| check:8efbf980357b794f | passed | 1bcf1047e7116d23c4f7fa3b6795bd39e2968b18ea59d30fb05cc11e6b83ede4 | False | 3026 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1392339733b148a3a0e3d347a1013543 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 5a486a4deddf0ecec2d161de34ef54db5c7c7a08f4d973358642213da0791531 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `5245eb67666e219dbd47d693a5f05568822962680054cc31dbc5838e5f7f9b78`
