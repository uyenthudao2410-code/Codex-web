# Orchestration Run Summary

- Run: `ba0c045deb6f465fa8ed546066d8f39a`
- Task: `4d23160f61624f77a9c605e2c58a8836`
- Objective: Verify the current R2B server-first auto-dispatch implementation already present in the worktree after the formatting recovery. Do not modify source. Prove formatting for the four touched files, core placement policy behavior, production root compilation, and test-graph type correctness. Preserve all unrelated worktree changes. This verification corresponds to the implementation originally written under R2B run 8493048d89c048aeaa44f45be14fbc14; the temporary formatting recovery run changed only formatting of validation_handoff.rs.
- Status: **accepted**
- Started: `2026-08-16T13:10:21.287Z`
- Finished: `2026-08-16T13:15:28.539Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9b5e4b1cd9de4bef902c3ca46ac705e5` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `7582c1cb858942619724d017e92f74b5` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 85d3ebb551b04c82a8337383fb478251 | 7582c1cb858942619724d017e92f74b5 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 768b6d97271613a797d8e7c68f039cd97cd1592fd162dbfb47ae9d22fd95bd81 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8307 | `deterministic` | `deterministic` | explicit_request |
| 8340 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8333 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `c5e566672ff720f89dc4fb30dc769cf3282600281374ba70549f87aa320c8f14`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
