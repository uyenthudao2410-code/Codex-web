# Orchestration Run Summary

- Run: `36b6631db5944c29b23b455d0f9b0795`
- Task: `15d958c0221e4823ae12900fc4103557`
- Objective: Fix the live Phase 3A Install runtime failure without changing supervisor policy. Normalize every custom PowerShell helper invocation that uses method-like `FunctionName(...)` syntax into idiomatic command syntax with a separating space/parenthesized argument, especially Assert-Manifest, Test-AbsoluteSafePath, Test-PathEqual, Get-Sha256File, and Get-Sha256Text in Install/Status/Uninstall/Run paths. Add a static regression to reject method-like calls for those helpers. Preserve all fail-closed health/restart behavior and unrelated runtime evidence. Prove PowerShell AST parse, focused supervisor tests, and full npm test.
- Status: **accepted**
- Started: `2026-08-16T08:45:31.036Z`
- Finished: `2026-08-16T08:46:38.905Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3d398b5a8c9f4915aee78724f80bd9aa` | `mcp_only` | `6299c052567852607ddcda30fabe48c859eef932` | replanned |
| 2 | `8133f1e17b504438b87b1565a03d9727` | `mcp_only` | `6299c052567852607ddcda30fabe48c859eef932` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 0de6f456f3534ca09280c30ac619b67b | 8133f1e17b504438b87b1565a03d9727 | accepted | 6299c052567852607ddcda30fabe48c859eef932 | 63e14582429307ac08bae5e398df495297924fabc9e64fb3a6821bb048dcdd31 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 6402 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6424 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 6418 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `96ad1d8eab742b569bd4899cd59cb5ff1f3ef0cb65eff7c936c9ef9dcaf2e0c0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
