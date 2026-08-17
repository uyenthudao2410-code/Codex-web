# Orchestration Run Summary

- Run: `967bb4c9007f4f8aac4f14eaf16ed521`
- Task: `42edf84cf6164690b3d016057c02f222`
- Objective: P1.1 only: identify the existing authoritative evaluator/report path that can generate a fresh canonical current-ledger baseline from .coding-tools/orchestration/ledger.sqlite3 without inventing a second analytics pipeline. The baseline must cover total runs; accepted/rejected/aborted/current states; first-pass vs repaired; TTAR p50/p90 where methodologically supported; replan counts; failure/error classes; route counts; pair counts; quality-outcome coverage; controller timing/usage/cost coverage; and host-bound span coverage or an explicit unavailable/not-yet-computed state if the current evaluator cannot derive it. Determine exact commands/files to use, source/runtime/fingerprint provenance to record, and whether any small evaluator/reporting gap must be fixed before generating the report. Do not mutate files in prepare. Preserve P0.2/P0.3 closure and do not publish/release.
- Status: **accepted**
- Started: `2026-08-17T14:51:35.465Z`
- Finished: `2026-08-17T14:58:49.958Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3d1671ab31ed4924baf2f53d52cea8e6` | `mcp_only` | `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 41cc3b9c15344ea3afaf328ba7b1b08f | 3d1671ab31ed4924baf2f53d52cea8e6 | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 8e6fc113b8a3dcfa05592f1afd3c7ecfc7e01613d6347dd9940b3c7d655ea9ce | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 14332 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `39`
- Chain head: `d179477d2d9974ba587c43a700e2aad53b5c56c5c6f6907ed24f3903da908886`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
