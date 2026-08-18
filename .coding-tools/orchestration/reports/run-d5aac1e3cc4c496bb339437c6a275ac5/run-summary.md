# Orchestration Run Summary

- Run: `d5aac1e3cc4c496bb339437c6a275ac5`
- Task: `a229f562ba334dd793d6e754b144cd08`
- Objective: Fix the Electron development supervisor so controlled Coding MCP restarts always launch the current workspace development source under E:\DEV\Codex-web\resources\coding-tools-mcp, never an installed/bundled fallback copy. Preserve packaged behavior. Add fail-closed development launch-root validation plus observable launch metadata sufficient to prove the Python executable/module root used by the supervisor. Add focused regression tests. Do not commit or push. After source verification, perform exactly one controlled runtime restart and verify smart-v3 tool_count=8, task_control.action includes solution_shadow, solution_shadow_recommendation exists, and tool contract SHA equals bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70.
- Status: **accepted**
- Started: `2026-08-18T11:57:04.160Z`
- Finished: `2026-08-18T12:01:47.072Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **4**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `bf31bc6cd5a44cb0b41df24fefb6e1db` | `mcp_only` | `d2f96e6200d736ca257d5f8a4a7b1fcb5e41ed9b` | replanned |
| 2 | `74d00b43d14144a2ac3b94acfa564c6f` | `mcp_only` | `d2f96e6200d736ca257d5f8a4a7b1fcb5e41ed9b` | replanned |
| 3 | `c45e892e1a55455c8f00c4df3a767602` | `mcp_only` | `d2f96e6200d736ca257d5f8a4a7b1fcb5e41ed9b` | replanned |
| 4 | `214b17e730984d8b867812f97d5055ef` | `mcp_only` | `d2f96e6200d736ca257d5f8a4a7b1fcb5e41ed9b` | replanned |
| 5 | `ceb18830ebad48cfb429619dbd21239f` | `mcp_only` | `c360eb953557456b19e0dff4f6ed5f6f8c44e7d7` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 616996f7a65547f29430a13f0b78aad5 | ceb18830ebad48cfb429619dbd21239f | accepted | c360eb953557456b19e0dff4f6ed5f6f8c44e7d7 | f373c9da7cb4324a1c822f46b8fdfeef68911f39fcffd4fcda09450c235d957a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 17721 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 17743 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 17765 | `deterministic` | `deterministic` | explicit_request |
| 17782 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 17732 | `CHECK_FAILED` | `PROVING` |  |
| 17737 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 17759 | `CHECK_FAILED` | `PROVING` |  |
| 17776 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `2efe589a74cf63d3b43114b61343f9a838b0be23fe7be9a53f2e2d78a4b7c21d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
