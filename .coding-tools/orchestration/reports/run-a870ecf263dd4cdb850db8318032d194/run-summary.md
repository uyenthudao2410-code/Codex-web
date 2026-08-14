# Orchestration Run Summary

- Run: `a870ecf263dd4cdb850db8318032d194`
- Task: `abbaf3100a8642c3906973af9e11566e`
- Objective: P3A semantic-safe required idempotency: close the first agent_workflow execute gap by using TaskState.task_id as the workflow operation epoch. Before auto-deriving a required agent_workflow execute key, validate the public schema, then ensure/reuse the current visible task epoch; preserve any nonterminal EOCL run even if TaskState status is unusual. Derive agent_workflow execute keys from operation + task_id + canonical request hash, not run/wave or transport request id. A completed/failed/stopped task with no live EOCL authority gets a new task epoch, so an intentionally new identical operation receives a different key. Keep task_control accept/reject run/wave + caller/fence semantics unchanged. Add end-to-end tests for initial auto-key, restart replay, same-task exact replay, and new task epoch allowing identical payload as a new operation.
- Status: **active**
- Started: `2026-08-14T18:10:30.457Z`
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
| 1 | `b674afb3cb2f45f59947ec47bea37530` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3276 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3284 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `d7fdaa5a3b5d6391d44ab5fb4ea120e33998895cbd0639751db9ab89a787cbad`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
