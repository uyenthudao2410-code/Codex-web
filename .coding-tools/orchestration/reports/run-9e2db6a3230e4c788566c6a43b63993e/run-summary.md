# Orchestration Run Summary

- Run: `9e2db6a3230e4c788566c6a43b63993e`
- Task: `47240f924f9041a48f38c283ca0b3bcd`
- Objective: Final delivery verification for the already accepted canonical-ledger read-only path safety fix before Git commit/push. Do not edit source. Re-prove the current worktree because runtime evidence changed the worktree fingerprint after prior acceptance. Preserve canonical root .coding-tools history; ensure resources/coding-tools-mcp/.coding-tools remains absent; do not stage or commit ledger.sqlite3-shm or ledger.sqlite3-wal; do not add heavy Excel/test artifacts. Run focused regression, module-size guard, repository coding-tools delivery gate, and git diff --check. No commit/push/restart in this wave; this is the final pre-commit authority proof only.
- Status: **accepted**
- Started: `2026-08-22T14:14:48.176Z`
- Finished: `2026-08-22T14:17:02.377Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `7ea116364fd44c7a87734dfa2310723c` | 1 | `run_initial_objective` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 2 | `ef75cda037a34a14a5ed7e6a0ec536b0` | 2 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 3 | `a7af67486be04a4381d7d4b6ec5b9711` | 3 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 52bca8ff42c0463e8b5c78481ddd7c24 | a7af67486be04a4381d7d4b6ec5b9711 | accepted | 6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0 | cb410d7551ec281d616cc5335476baaae468b3fd0820234be236eb6cf5c9cb3a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27346 | `deterministic` | `deterministic` | explicit_request |
| 27373 | `deterministic` | `deterministic` | explicit_request |
| 27390 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27367 | `CHECK_FAILED` | `PROVING` |  |
| 27384 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `42b5bd8feef842007327b6fc10442d62b75b187b0fbf84ca1dcf6af2980c3c4f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
