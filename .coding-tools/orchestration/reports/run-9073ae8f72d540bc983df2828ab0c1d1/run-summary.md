# Orchestration Run Summary

- Run: `9073ae8f72d540bc983df2828ab0c1d1`
- Task: `729f8b2fccb04057859bcff75ed869c1`
- Objective: Complete concurrent multi-project execution-context isolation in E:\DEV\Codex-web without breaking the intended multi-root UI contract. Root cause already proven: HTTP MCP sessions currently alias one shared Runtime whose TaskStateStore and projection helpers are workspace-global, so independent ChatWeb tabs/projects can overwrite task-state.json/projection and can accidentally fall back to another tab's current_active_run. Keep one shared Runtime/process, orchestration ledger, resource governor, command registry, and authorizedRoots semantics. Introduce a lightweight stable execution-context/task projection scope for stateful MCP clients so independent tabs/sessions have isolated TaskStateStore projections while reconnect/aliases for the same logical context can resume. Legacy/stateless clients must remain compatible and may use the legacy workspace-global projection when no stable context exists. Scope must propagate into long-running/background agent_workflow workers, not only HTTP thread-local request handling. A scoped context with no projected run must never fall back to an unrelated workspace-global current_active_run. When a new orchestration run is created for a scoped ChatWeb context, controller ownership must bind to the initiating scoped controller identity so another tab cannot opportunistically claim it. Authorized roots remain valid full execution roots and must not invalidate primary-workspace session scope; actual primary workspace switch still invalidates stale workspace-scoped sessions. Preserve all existing unrelated worktree changes, P4/economics changes, renderer changes, telemetry and docs; do not reset/restore/clean, commit, push, restart or deploy. Keep smart-v3 exactly 8 public tools. Add focused regression tests proving: (1) two independent stateful ChatWeb sessions in the same primary workspace can start different tasks/runs and each reads its own projection, (2) actions in session B do not mutate session A's task state/events/run projection, (3) background agent_workflow retains the initiating execution context, (4) a scoped empty context does not attach to another active run, (5) authorized-root execution remains valid without switching the primary workspace, (6) same-context reconnect continuity remains valid, (7) actual workspace switch rejects stale scoped sessions, and (8) legacy unscoped/sessionless compatibility remains intact. Also replace the positive authorized-root regression command using inline `python -c` with a harmless command allowed by the safe permission mode (for example `python --version`) so the oracle tests product semantics rather than permission escalation.
- Status: **aborted**
- Started: `2026-08-19T05:27:06.505Z`
- Finished: `2026-08-19T05:27:45.191Z`

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
| 1 | `3831c023e19645bb8e498be8a6c64bb7` | `mcp_only` | `7c1c93ea72fa3465d718f7826494629426c1a9e8` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 20163 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 20174 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `4091f4a9bc31f54209a862599a970ccad4bf78e951b0134b7bc818d05cc83691`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
