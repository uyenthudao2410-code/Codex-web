# Orchestration Run Summary

- Run: `7684bd70d5ec45c68f0a5a03615fa653`
- Task: `3a62d3356aa94316bac33315aaf233e9`
- Objective: C5 historical prior-artifact build only, continuing after accepted current-lifecycle checkpoint b51dd665a3dc4db7ac5c73d93f160f02, C5 contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc, and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. Current source remains main/origin HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f. Reproduce the legitimate prior 0.3.4 source at exact commit 026f79b3ab5997cb15f38a3b41769da6a79d790b in external worktree C:\Users\Admin\AppData\Local\Temp\codex-web-c5-prior-026f79b3. Network is forbidden: dependency installation must use npm --offline only, Electron 43.2.0 and electron-builder/NSIS caches were preverified locally. Build the repository-defined prior NSIS artifact only if fully offline succeeds; hash and copy the resulting web-mcp-assistant-setup-0.3.4.exe into C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34\artifacts. Do NOT install or launch 0.3.4 and do NOT claim upgrade/rollback: the real user profile contains a pre-existing legacy Trợ lý Web MCP shortcut SHA256 393337c654c77795dad8a847a259391364635ed058e75603314b8321200c5957, the prior/current packages share appId com.gptwebcodex.assistant, and Windows Sandbox is unavailable, so host-side upgrade/rollback is not safely isolated. Preserve main source bytes, all .coding-tools evidence and unrelated work. No normal UI, production profile/descriptor/task writes, C4 rerun, network, publish/tag/release/deploy, or forbidden ACK.
- Status: **accepted**
- Started: `2026-09-06T06:01:32.351Z`
- Finished: `2026-09-06T06:04:35.146Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `3618a4ff5cc4417ab52ea48ee0856d92` | 1 | `run_initial_objective` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | replanned |
| 2 | `e8bd790c2ecc4aeb9f45c736c7a2b772` | 2 | `replan_request` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f549bc0102e24c028c07e9ad48c034a7 | e8bd790c2ecc4aeb9f45c736c7a2b772 | accepted | 9e752e34db745cd4fb2d0830a517910eced9c37f | 8cdbebc9f4796a5d0d324214f7656aa3e5d433f9feb27402c0f2861fb6243b80 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41748 | `deterministic` | `deterministic` | explicit_request |
| 41783 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41773 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `2673ebda23130a050414a5f0813b71cd51f7d7274ff913d95f592f9674d45129`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
