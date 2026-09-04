# Orchestration Run Summary

- Run: `9fc19ad0412447d2b502acc347d8108f`
- Task: `e2f729d1c70a468ab636ffad1ab6ae8e`
- Objective: Complete the second half of the proven preserve-then-remove remediation for GitHub delivery. The current misplaced ledger has already been losslessly preserved and controller-accepted at checkpoint 31d0e8d9bf734292af158cde728e39bc. Remove only resources/coding-tools-mcp/.coding-tools, verify it is absent, run the previously failing source-bundle test, run the complete Coding Tools MCP pytest suite, and rerun repository history/secret/diff guards. Do not modify product source, do not reset/restore/clean/rebase, do not commit or push yet.
- Status: **active**
- Started: `2026-09-04T01:40:49.464Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ca698feedaac4cd7a189ffbb5c11173c` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 2 | `7c45ce0229894d908b9d42888812ba62` | 1 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 3 | `47cc4adc6ea447d6b904a9da3613815f` | 2 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 39366 | `deterministic` | `deterministic` | explicit_request |
| 39386 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 39376 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 39415 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `84`
- Chain head: `ee60a67848e2daa9a4a922fb6699bb5814bc249304a855b2ff535e9c928134b5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
