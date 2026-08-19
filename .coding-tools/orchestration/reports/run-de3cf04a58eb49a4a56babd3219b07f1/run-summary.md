# Orchestration Run Summary

- Run: `de3cf04a58eb49a4a56babd3219b07f1`
- Task: `506b0d7a24764be28f63c10b49d1dda8`
- Objective: Finalize the corrected multi-root workspace contract in E:\DEV\Codex-web. Primary workspace remains the control/runtime/session identity. Explicit authorized roots are valid execution scopes for agent_workflow and exec_command without switching the primary workspace. Only paths outside both primary and authorized roots fail pre-mutation with STALE_WORKSPACE_CONTEXT. Session scope remains primary-workspace-only, so authorized-root changes keep the session valid while an actual primary workspace switch invalidates a scoped stale session. Preserve unrelated changes. No restart/commit/push.
- Status: **active**
- Started: `2026-08-19T05:06:32.688Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1f64ce026f384c3baa19221930a275cf` | `mcp_only` | `7c1c93ea72fa3465d718f7826494629426c1a9e8` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 19767 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 19778 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `58e48d701da6e5ee1e2bc22b5f2971e7b3652593e7170ba912fd5657de89f37c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
