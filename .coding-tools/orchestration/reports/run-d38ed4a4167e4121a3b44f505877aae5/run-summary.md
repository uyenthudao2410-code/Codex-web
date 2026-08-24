# Orchestration Run Summary

- Run: `d38ed4a4167e4121a3b44f505877aae5`
- Task: `335a2c36348d42b2bd9a010e98fd59f6`
- Objective: RUN-MW-CLOSURE: verify exact multi-workspace isolation, durable context, and scoped control on the current Codex-web worktree.
- Status: **aborted**
- Started: `2026-08-24T11:54:12.993Z`
- Finished: `2026-08-24T12:03:56.806Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0548a9073c4a4ab692d47540297433df` | 1 | `run_initial_objective` | `mcp_only` | `4d77edd521658d14d6f5125b1e8ff3498e80a77f` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28859 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28875 | `SOL_REJECTED` | `ACCEPTING` | Live handoff capsule lacks the required base_head/worktree_fp/write-lease provenance because the stateless task context is not propagated into the background agent_workflow thread. Replan after the scoped-context propagation fix and focused regression. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `f67dbf70ff68a15157f07daa37c9f814c3cab3c76e8c067cd3d972743a8818a0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
