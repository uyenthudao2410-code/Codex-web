# Orchestration Run Summary

- Run: `0d3dc1349077416680946c08c76875ef`
- Task: `9d4f5695eb3d4b37a6684f3bd3a8d894`
- Objective: Complete P0.2 coherence using only the product-native authenticated Recovery Host IPC. Instantiate RecoveryIpcClient with createRuntimePaths for the current %APPDATA%\web-mcp-assistant data root; call lightweightSnapshot(), which internally performs authenticated primary Coding MCP health. Output only content-free snapshot fields, never the descriptor token. Require primary mcpRunning/nativeAlive/tunnelRunning/fullyReady all true; require device.coding endpoint_device_instance_id equals current device_instance_id; require device.recovery host/mcp/tunnel all healthy; independently require Recovery MCP /healthz ok with matching device_id/device_instance_id; require exactly one listener each on 18766,18767,18082,18083 with source-tree native-python/tunnel-client executables; inspect tunnel command lines internally and output only boolean endpoint/health-port matches; require Recovery Supervisor healthy/alive and exact Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Also require the failed temporary helper directory/result are absent. No mutation.
- Status: **accepted**
- Started: `2026-08-17T08:59:47.782Z`
- Finished: `2026-08-17T09:00:16.188Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `68c8cab1593f46249c3f801d7e85cdcf` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 1392339733b148a3a0e3d347a1013543 | 68c8cab1593f46249c3f801d7e85cdcf | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 5a486a4deddf0ecec2d161de34ef54db5c7c7a08f4d973358642213da0791531 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12927 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `5245eb67666e219dbd47d693a5f05568822962680054cc31dbc5838e5f7f9b78`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
