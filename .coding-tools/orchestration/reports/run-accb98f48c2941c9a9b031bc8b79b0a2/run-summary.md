# Orchestration Run Summary

- Run: `accb98f48c2941c9a9b031bc8b79b0a2`
- Task: `f4435a9633d743278c90d076381a3bf6`
- Objective: Close the F4/F6 real-process tunnel recovery proof gap with an explicit test-only patch. Add a Node-based tunnel fixture whose run process owns the real loopback health listener and whose health command validates the exact expected PID without any external network. Add F4 Recovery Plane proof that killing only Recovery Tunnel produces a new tunnel PID while Recovery MCP PID/device identity/ports remain unchanged. Add F6 primary RuntimeOrchestrator proof that recoverTunnelOnly replaces only the primary Tunnel while the real Coding MCP process/workspace/device identity remains unchanged, using a loopback-only manual proxy. Do not modify production source or unrelated dirty files.
- Status: **accepted**
- Started: `2026-08-17T11:03:41.258Z`
- Finished: `2026-08-17T11:05:46.935Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `bc477635dbcf4525b76b2cd6db857007` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| bc9cc4ca25cb40d191c4882c98c60373 | bc477635dbcf4525b76b2cd6db857007 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 74284b4c64d0c4cdee06d460fa7944f50ee0012db1e3f8fcb2b9f16f129fd0db | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13674 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `bd441ed7820a1dd6b941667188e7e33eee7de3604a6ee8ee274f485fc057ba2a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
