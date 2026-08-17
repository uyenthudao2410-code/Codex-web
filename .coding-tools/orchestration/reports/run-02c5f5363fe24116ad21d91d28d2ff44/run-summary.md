# Orchestration Run Summary

- Run: `02c5f5363fe24116ad21d91d28d2ff44`
- Task: `a5842da2d14f4a39a36007dcca86e000`
- Objective: After the user-requested Electron-supervisor runtime restart, verify the new runtime is actually active and identify any remaining live errors before resuming the main unfinished work. Read-only diagnosis only: do not modify source or Git. Verify Recovery Host descriptor/device identity, Native/Coding MCP and Coding Tunnel ownership state, Recovery Plane ownership state, live lightweight snapshot readiness/device/Git projection, recent runtime logs, and rerun the focused M1.2 regression suite. Report only concrete failures or residual risks.
- Status: **accepted**
- Started: `2026-08-17T04:16:31.290Z`
- Finished: `2026-08-17T04:22:26.993Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f457b0980ace425b88b233641aadb1aa` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | replanned |
| 2 | `13ce060a21b14e0fb7c118701a3c3363` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | replanned |
| 3 | `2543a96612a049ec9aa33e3b6555a144` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| cbf0c026b8b343b296e439f6b3b5c542 | 2543a96612a049ec9aa33e3b6555a144 | accepted | 3a3abaff72a8e6382e4c362865becba069e4ecfc | c57cbdc9db4da8b82ee843b00766c26b8f6f14fc4b81ad365cde7aaffef021e4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11257 | `deterministic` | `deterministic` | explicit_request |
| 11276 | `deterministic` | `deterministic` | explicit_request |
| 11300 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 11268 | `CHECK_FAILED` | `PROVING` |  |
| 11292 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `72`
- Chain head: `e1b365beb762c76f853d956e62efa9efc304029a99e59e684a1f0196bad1a37b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
