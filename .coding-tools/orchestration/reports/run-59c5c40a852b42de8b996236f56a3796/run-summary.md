# Orchestration Run Summary

- Run: `59c5c40a852b42de8b996236f56a3796`
- Task: `8f122cf6823a4beabdce014b40bd1ccb`
- Objective: Finish pre-EOCL patch-preflight idempotency semantics. Tag every ToolFailure raised by the preflight call, including patch-parse failures before dry-run, as a known no-write terminal outcome; keep all post-preflight exceptions unchanged. Extend the focused regression with malformed patch syntax. No routing, provider, review, restart, or acceptance-policy changes.
- Status: **accepted**
- Started: `2026-08-15T05:32:59.171Z`
- Finished: `2026-08-15T05:33:56.371Z`

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
| 1 | `bb40ed078f8f4f8cbe6c34c03d9f8cef` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 30bfe8e8031b4933b7f92d82b9ce7ec0 | bb40ed078f8f4f8cbe6c34c03d9f8cef | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 657ad44fa3c4582e9f81d113cb8f32b7f2452cb6bcae4440ab66f3e8b78f0f74 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4459 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `8f3679b9329c47c3fc1cacd2ac3e4ccf8664664f25c1e306d23c2c2739880e99`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
