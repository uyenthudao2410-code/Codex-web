# Orchestration Run Summary

- Run: `92834371fba3419a8c0e065609835251`
- Task: `0d325c5daad74999a2fcd49d1a59a74b`
- Objective: Apply the supplied one-file test-harness patch exactly, then verify it. The patch removes process-global WEBCODEX_MCP_MODEL_SURFACE dependence from ordinary MCP test runtime construction while preserving explicit env-selection tests. Do not modify production code or any other file.
- Status: **active**
- Started: `2026-08-13T17:43:33.434Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3a7804be77e348deb9bc68580b3b33b9` | `mcp_only` | `db7725e3601afc2692627a0b4eef674d599bd17e` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 442 | `auto` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 449 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `fdfae5a031a1fcbc4e7a0080a0a1f03e653cef1359b0c6d1260d078d33641130`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
