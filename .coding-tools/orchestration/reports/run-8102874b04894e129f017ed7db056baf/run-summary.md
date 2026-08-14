# Orchestration Run Summary

- Run: `8102874b04894e129f017ed7db056baf`
- Task: `8567b186bfe547349e02ab0af10af44d`
- Objective: P2B runtime projection reconciliation: after startup stale/terminal ledger reconciliation and after OrchestrationControl is available, reconcile the persisted TaskState orchestration projection with the authoritative run row. If the projected run is terminal, map accepted->CHECKPOINTED, blocked->BLOCKED, aborted|stale->ABORTED, use the latest durable wave id, clear write lease/owner fields, and emit orchestration_projection_reconciled. Do not change task objective/history, do not turn stale proof into acceptance, and do not touch active runs. Expose a bounded boolean recovery flag in workspace_context/task_control recovery. Add focused test with a stale parent + lingering ACCEPTING TaskState proving fresh Runtime repairs both child wave and projection while preserving run status stale.
- Status: **active**
- Started: `2026-08-14T18:04:27.897Z`
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
| 1 | `16c598fede4e4befb16eaad4247a307b` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3237 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3245 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `eb04697fe04123511be28e80976684e05bb5b4540a1898f48f7955f84f2eba73`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
