# Orchestration Run Summary

- Run: `5e7544aa62bb43a4b9ea25c4f0671acb`
- Task: `374813dbc1be41489a9e67c32748f4f4`
- Objective: Preflight exactly the six currently reported unresolved stale orchestration RUN IDs using the repository-supported read-only exact-ID maintenance CLI. Capture immutable snapshot/logical hashes and blocker classifications only. Do not reconcile, do not pass runtime-stopped, do not modify source/Git/ledger except ordinary current RUN evidence, and do not inspect any other historical RUN.
- Status: **accepted**
- Started: `2026-09-07T02:30:52.213Z`
- Finished: `2026-09-07T02:33:06.124Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `dbba59bcc81446b38c51dadcbd36f2de` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 2 | `d539d830be174302bc9ec10d14bf6de0` | 1 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 3 | `df21e6cd14c344aaba02959c010db129` | 2 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3e9dbd58e33c4c5fbe49ac597d39d597 | df21e6cd14c344aaba02959c010db129 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 8eae821957ecf374cce4dd8d767c77a843978f8673e7bcba03cd9b7d9f59e1a4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42620 | `deterministic` | `deterministic` | explicit_request |
| 42644 | `deterministic` | `deterministic` | explicit_request |
| 42668 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 42634 | `CHECK_FAILED` | `PROVING` |  |
| 42658 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `74`
- Chain head: `675c0f0af65252c437cd3e7955b11cc12bed2eb4fd0915cd07645de3ff109f9c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
