# Orchestration Run Summary

- Run: `183985ff1e3a47e287c9a9ad16f35bf7`
- Task: `df5208b23242455a87a1f92ab0fca853`
- Objective: Remove the final dead legacy measuredUsage helper from renderer/dashboard.js and update the focused dashboard regression so the helper must be absent while renderAll remains locked to canonicalMeasuredUsage. Preserve all unrelated WIP and canonical token semantics. No restart, commit, push, or live activation.
- Status: **accepted**
- Started: `2026-08-19T11:34:11.417Z`
- Finished: `2026-08-19T11:36:08.786Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `218964d6c62b46e19c36fcc3407bd73b` | `mcp_only` | `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02` | replanned |
| 2 | `244b12d5c1b64e8a9f679e1043d457af` | `mcp_only` | `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 74c59804493d4cc2b71e07896893f842 | 244b12d5c1b64e8a9f679e1043d457af | accepted | 17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02 | a0c58073ef1a60942843c1e158eb2afd6d03cf1c0ac9d9de24c9fc04ea369f40 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 21700 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21719 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 21712 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `14148f67c4fde5dee121842e53922204df88e42735f56718d7601e90544c2f3c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
