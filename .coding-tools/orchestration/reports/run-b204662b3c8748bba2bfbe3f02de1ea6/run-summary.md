# Orchestration Run Summary

- Run: `b204662b3c8748bba2bfbe3f02de1ea6`
- Task: `4cefad2d893b4dbc8fcaf5263328452a`
- Objective: S4/W5 paired-evaluation gate, proof-only and no source/docs mutation. Use the repository's existing compare_route_policies.py CLI against the real current .coding-tools/orchestration/ledger.sqlite3. Baseline policy is chatweb_mcp (current preparation flow); candidate policy is context_compiler_shadow (new compiler treatment). Require min_pairs=10 and min_task_classes=4 to match the maintained W5 representative strata. Do not create synthetic/benchmark/replay tasks and do not mutate the ledger to manufacture pairs. Also prove the evaluator's zero-pair and missing-total-cost fail-closed behavior with existing focused tests. If the real ledger lacks complete comparable representative pairs, the accepted stage decision must be KEEP_SHADOW / NO_PROMOTION and auto-injection remains unavailable. No S5.
- Status: **accepted**
- Started: `2026-08-21T00:16:45.458Z`
- Finished: `2026-08-21T00:17:58.727Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2165d6ccafb94ef4b5ce05ee6984b18d` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 9cd2827246e94720b12b95f8048a40c4 | 2165d6ccafb94ef4b5ce05ee6984b18d | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 7ac923d94f71d76598b6b7bbcaf0593fd5004019ccaffec5806ae3e954494827 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 24812 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `59c92edd2f339e4fda7505fdee040e04dd88cd1f5687ed01988eea133a72a402`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
