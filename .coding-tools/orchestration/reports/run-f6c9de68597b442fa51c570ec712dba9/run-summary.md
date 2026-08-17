# Orchestration Run Summary

- Run: `f6c9de68597b442fa51c570ec712dba9`
- Task: `7f46ca46e8e64a57bd5b84dc681f698f`
- Objective: READ ONLY. Diagnose the Coding MCP connection/runtime routing architecture responsible for one ChatGPT plugin session landing workspace_context on E:\DEV\Tools-Codex-web while exec_command/agent_workflow land E:\Github\Tools-Codex-web. Do not mutate. Localize HTTP session creation, runtime selection, workspace switching, hub client identity, Electron supervisor registration/health/restart, and any stale endpoint/fallback behavior. Recommend the smallest fail-closed session-affinity fix with exact files/symbols and focused tests.
- Status: **accepted**
- Started: `2026-08-17T03:26:33.747Z`
- Finished: `2026-08-17T03:50:01.397Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `7cf8805da9b34e25a4a4db38e429fa63` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | replanned |
| 2 | `d69559cfe6244c4ba3238d68f91081e3` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 842a487f86504880b2620e78ae920fdd | d69559cfe6244c4ba3238d68f91081e3 | accepted | 3a3abaff72a8e6382e4c362865becba069e4ecfc | 378aade8e4cf123b3b2dda195605895a381445a3a9503e3eda2eade580fec036 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11096 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 11077 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `58`
- Chain head: `fdfe464941c3fc0c9026005fd8647c435a1d4aac3b3b933cab9d7887ae7d9332`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
