# Orchestration Run Summary

- Run: `db0044df05c948b5a40c63fc52d2ad16`
- Task: `5899f563538f40cbbedf279eae7d57b1`
- Objective: Commit and push the fully accepted canonical-ledger path safety and WAL-safe delivery fixes to origin/main. Preserve all canonical .coding-tools evidence, excluding only the two approved ledger.sqlite3-shm and ledger.sqlite3-wal sidecars. In a single delivery command so no controller event can land between final staging and push: restage the exact source/doc change set; run WAL-safe evidence staging; run mandatory delivery guard and cached whitespace check; create the main fix commit; run WAL-safe evidence staging and guard once more for push-time evidence; create a final evidence checkpoint commit (allow-empty is acceptable if no post-commit evidence delta); push main without force; print local HEAD and remote main SHA. Do not restart runtime in this wave.
- Status: **active**
- Started: `2026-08-22T14:26:25.418Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `c1cbc51f3a4840caafbd5cb429db288a` | 1 | `run_initial_objective` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 2 | `b18739a6e2b74fcb81fb6b4d910658a9` | 2 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27501 | `deterministic` | `deterministic` | explicit_request |
| 27518 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27512 | `CHECK_FAILED` | `PROVING` |  |
| 27529 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `e744535afac5fee3c206258c023d3414120c06278719db68c7b671c03024ccf7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
