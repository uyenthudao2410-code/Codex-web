# Orchestration Run Summary

- Run: `02e6ab7520aa44f0a62a7dc23edf8923`
- Task: `2a507b4dc30c4beeafdd4f8f3fbafb90`
- Objective: Fix the proven deferred-observer defect only in scripts/full-clean-activation.js: in waitForReplacementOperation, recover from missing ephemeral code.activation_status only when the durable bootstrap result is completed and its exact operation/epoch agrees with replacement descriptor epoch, projected status epoch, and observed status operation ID. Reuse the bootstrapResult object as operation. Preserve failed/expired UPDATE_INCOMPLETE, pending polling, and all mismatch guards. Add the focused regression in tests/full-clean-activation-command.test.js. Preserve all unrelated WIP.
- Status: **accepted**
- Started: `2026-09-08T21:01:03.590Z`
- Finished: `2026-09-08T21:03:53.427Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `61f6aa46f29044498b67330d1546190c` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a80af312e2a4450aa59d5a28539eec53 | 61f6aa46f29044498b67330d1546190c | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 597b6d914aa043de8ba0da824fb448a85dc1e3a990e8adefa427f0cdb2f888b5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44744 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `96e95ba4f5158dfeaeb7c5ace76cb1c36075ac74610f71eeea4b948bd24df047`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
