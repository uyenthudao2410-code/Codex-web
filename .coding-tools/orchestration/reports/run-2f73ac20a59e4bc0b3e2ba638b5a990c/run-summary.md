# Orchestration Run Summary

- Run: `2f73ac20a59e4bc0b3e2ba638b5a990c`
- Task: `55d79a1c9872428dbe4ad0593ba77358`
- Objective: Start the local WebCodex native semantic provider for E:\DEV\Codex-web from the repaired machine state at C:\Users\Admin\AppData\Local\WebCodex\g4-semantic\codex-web-current, then verify a webcodex process remains alive. Do not modify repository source, Git, ledger, activation configuration, or release artifacts.
- Status: **accepted**
- Started: `2026-09-07T02:17:28.884Z`
- Finished: `2026-09-07T02:23:15.628Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `372b9ae942c14d54bed96108f117d49a` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 2 | `20c0618be24148de938f7a27d9e407ee` | 2 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 3 | `47fd2ca4c25547f2839461337810f1cf` | 3 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 4 | `7db43b5436314655a0e0a6f92ae85730` | 4 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | replanned |
| 5 | `e52d04e29f3644c69241b99d50789251` | 5 | `replan_request` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 27395078dc3941c4b610d896ebc57f5d | e52d04e29f3644c69241b99d50789251 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | a3edd1cd514d1242901338c555ddd393cf8d95c344e579e091eeeef9514c3910 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42385 | `deterministic` | `deterministic` | explicit_request |
| 42414 | `deterministic` | `deterministic` | explicit_request |
| 42438 | `deterministic` | `deterministic` | explicit_request |
| 42464 | `deterministic` | `deterministic` | explicit_request |
| 42493 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 42404 | `CHECK_FAILED` | `PROVING` |  |
| 42428 | `CHECK_FAILED` | `PROVING` |  |
| 42454 | `SOL_REJECTED` | `ACCEPTING` | Evidence disproves a stale credential filename: configured connector-key exists, but semantic localization remains NATIVE_LSP_BINDING_INVALID and no WebCodex process remains alive. The repair objective is not met; replan must inspect the exact credential validation/startup contract rather than accepting a path-only check. |
| 42483 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `139`
- Chain head: `27e07c13675e7babc01a534fac9e304ceff482c33898fdad217869a5037c5f98`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
