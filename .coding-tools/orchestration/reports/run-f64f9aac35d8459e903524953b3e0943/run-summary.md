# Orchestration Run Summary

- Run: `f64f9aac35d8459e903524953b3e0943`
- Task: `4851cf6d899c4d9d8c23a988f3152ca1`
- Objective: Record only the clean final P0.2 rollback verification. On exact HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, verify Recovery Supervisor Scheduled Task is absent, %LOCALAPPDATA%\WebMcpRecoverySupervisor is absent, recovery-supervisor-status.json state is uninstalled, and %LOCALAPPDATA%\WebMcpAcceptance-0.3.4 remains present. Through shipped RecoveryIpcClient.lightweightSnapshot require primary mcpRunning/nativeAlive/tunnelRunning/fullyReady all true, recovery host/mcp/tunnel all healthy, and exact Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Independently require exactly one listener on 18766/18767/18082/18083 with expected source-tree executable families and Recovery /healthz ok. Run no unrelated tests and make no mutation.
- Status: **accepted**
- Started: `2026-08-17T09:02:41.645Z`
- Finished: `2026-08-17T09:03:16.021Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `855626394161448fa5ea98ed60c61c62` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 11007e2b3be6411dbffc5d507351b07d | 855626394161448fa5ea98ed60c61c62 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 89ded2b4753bd945a0e83d3d220b8eb1cbb5d9bebc52a9bf97ed7006c34a8329 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13013 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `71520990da4f1e0beb24980513c1bbb7327c01cf9cb680cc3381a070cf959209`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
