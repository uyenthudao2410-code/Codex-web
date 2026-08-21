# Orchestration Run Summary

- Run: `1b4ecb6beb324d3f9d87d506c6b682b8`
- Task: `a965a9efeb1e4738b654b33ce81cd6e4`
- Objective: Execute the final P1.1 exact-fingerprint RC source/security matrix on the newly accepted harness-compatible worktree. Run all maintained non-packaging gates in fail-closed order: diff hygiene, full Node/Electron tests and source-root-clean guard, full Coding MCP pytest, Recovery E2E, OpenCode Flash preflight only with no provider dispatch/cost, and production dependency audit. Do not mutate source/docs, do not build final installer yet, do not commit/push/restart/deploy/release/tag/publish, and preserve the resident codex-app-server and all .coding-tools evidence.
- Status: **accepted**
- Started: `2026-08-21T04:09:29.755Z`
- Finished: `2026-08-21T04:12:13.716Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6ba9213f91cb4b038cf65f0673640220` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `ffd9649586154313956ed356b18f6547` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2e3b5d800ddc4456b822912922656ab7 | ffd9649586154313956ed356b18f6547 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 555d63dd0f169540d9c34772396b4193ba0899ead582df55775f24030a95c649 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25747 | `deterministic` | `deterministic` | explicit_request |
| 25770 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 25763 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `16fdcef5028739369547124b45fb8b48e2874a0403c7972dc2f481620855f428`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
