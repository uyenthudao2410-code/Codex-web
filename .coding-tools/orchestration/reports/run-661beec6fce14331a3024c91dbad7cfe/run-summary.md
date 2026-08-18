# Orchestration Run Summary

- Run: `661beec6fce14331a3024c91dbad7cfe`
- Task: `cb18b9d9a22f4800b424ffd185fe3986`
- Objective: Remove only the proven-stale .git/index.lock, then create and push a point-in-time snapshot of every current deliverable change in E:\DEV\Codex-web to origin/main. Exclude exactly .coding-tools/orchestration/ledger.sqlite3-shm and .coding-tools/orchestration/ledger.sqlite3-wal through the accepted repository policy; keep ledger.sqlite3 and all other .coding-tools evidence. Do not tag, release, force-push, reset, clean, or alter the fsmonitor daemon.
- Status: **aborted**
- Started: `2026-08-18T11:40:24.868Z`
- Finished: `2026-08-18T11:47:19.603Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **4**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a3933825d0dc46fcb7a695fcd96550c4` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 2 | `725aace9399a4297bd0507d45acbf656` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 3 | `ac4df59e7f564bee8eb4cb3035e23907` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 4 | `d20fb65d669a49788bec90e6a4c01097` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 5 | `905aec65e7ba415fa2b4c02c3e50370b` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 17553 | `deterministic` | `deterministic` | explicit_request |
| 17578 | `deterministic` | `deterministic` | explicit_request |
| 17600 | `deterministic` | `deterministic` | explicit_request |
| 17617 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 17564 | `CHECK_FAILED` | `PROVING` |  |
| 17572 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 17594 | `CHECK_FAILED` | `PROVING` |  |
| 17611 | `CHECK_FAILED` | `PROVING` |  |
| 17628 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `85`
- Chain head: `580a310c4b114fbaf306b3fc3bb201fd3da90b1ead20787ed85502da588c9768`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
