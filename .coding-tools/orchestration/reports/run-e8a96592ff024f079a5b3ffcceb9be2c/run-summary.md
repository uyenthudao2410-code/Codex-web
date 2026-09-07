# Orchestration Run Summary

- Run: `e8a96592ff024f079a5b3ffcceb9be2c`
- Task: `7b0cbd6920cf44e198076a80fa3df447`
- Objective: C4 corrective Wave 2: honor Electron's explicit --user-data-dir only for Recovery Host mode so isolated packaged recovery uses its temporary profile; preserve the existing production %APPDATA%\web-mcp-assistant pin for normal UI and Recovery Host launches without an explicit override. Add a focused pure regression test. Do not modify the packaged smoke harness or unrelated files.
- Status: **aborted**
- Started: `2026-09-06T04:29:58.429Z`
- Finished: `2026-09-06T04:30:24.144Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `67827748f6c246f4b31d38c703c6b2fa` | 1 | `run_initial_objective` | `mcp_only` | `9b3241ddc963a77d916edc453ea7b7e8e4ae5391` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41348 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `61f0a366bc4f7180f0bbcb9870fe85064c814e908895bc616dc00c9fe8bd00a6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
