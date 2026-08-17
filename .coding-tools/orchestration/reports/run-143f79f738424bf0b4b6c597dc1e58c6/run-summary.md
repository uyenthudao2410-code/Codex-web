# Orchestration Run Summary

- Run: `143f79f738424bf0b4b6c597dc1e58c6`
- Task: `1fae209da80249588660824434d4a5ba`
- Objective: Selectively commit and push the accepted P0.2 current-session closure evidence on main. Preconditions: current source HEAD is acaa3582052ab6836ade7b55bd1ff2178ebc5117 and docs/PRODUCTION_CLOSURE_ROLLOUT.md has accepted P0.2 closure changes. Stage only docs/PRODUCTION_CLOSURE_ROLLOUT.md, .coding-tools/orchestration/ledger.sqlite3, and report directories run-c6235e7dfefe4df9938bf6d0b4c11bca, run-1151d304b5864708ad6f694d9fd91b6c, run-dfc0f3be347540989489dbf10574b48f, run-44add57e789e4b14bcef1588f0e371b9, run-f8219ca3acf8470ca39a86bedf546dad, run-0d3dc1349077416680946c08c76875ef, run-f64f9aac35d8459e903524953b3e0943, run-cb0a385d21464d02a9cb557a46433dea. Explicitly exclude .coding-tools/evaluation/chatweb-host-observations.jsonl, .coding-tools/performance.json, .coding-tools/task-history.json, .coding-tools/task-state.json, SQLite -wal/-shm, run-6ed664ad4eb2419ab27ca659519933a4 and all other unrelated report directories. Before commit require git diff --cached --name-only contains only the allowlist prefixes and includes ledger.sqlite3 and the living plan; require git diff --check --cached PASS. Commit message: docs: close P0.2 installed recovery acceptance. Push main to origin. After push print HEAD and origin/main plus concise status. Do not stage/reset/clean unrelated changes.
- Status: **accepted**
- Started: `2026-08-17T09:07:03.756Z`
- Finished: `2026-08-17T09:08:37.621Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9bf82ce8a7a147778c4e3f6acc1fc712` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 2 | `8f59745f71714133aa645f17415fe1db` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c7b8300b6ce84c48a84f03f9fd3bc690 | 8f59745f71714133aa645f17415fe1db | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | fa63d3911d6066231e14ff8d14632fab88ba5773205dab098fe0a9fab59d3c46 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13073 | `deterministic` | `deterministic` | explicit_request |
| 13092 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13084 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `3a6ae1aa9e8b37ea20ece7e13cce08c8527c058e728b95fefd7302871c363547`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
