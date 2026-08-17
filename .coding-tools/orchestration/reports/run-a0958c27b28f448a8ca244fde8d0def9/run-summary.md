# Orchestration Run Summary

- Run: `a0958c27b28f448a8ca244fde8d0def9`
- Task: `c1428f5b93e447b0a99b9dfe0afed542`
- Objective: P1 Server-First real-process acceptance on Windows for exact product source HEAD 3a3abaff72a8e6382e4c362865becba069e4ecfc. Use the already-proven exact-source webcodex-server and webcodex-runner binaries. First run the maintained PowerShell harness syntax gate, then run the full loopback-only scripts/e2e_server_first_snapshot_ws.ps1 canary. Acceptance is entirely the harness's fail-closed assertions: exact binary identity, two distinct source/compute runners, immutable SourceSnapshot transfer, validation on compute, safe proof identity, no durable raw source, ephemeral checkout cleanup, and unchanged authoritative checkouts. Do not mutate repository source, Git refs, external services, or network resources.
- Status: **active**
- Started: `2026-08-17T02:09:40.203Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `cce1305759c74068bbd83062d453fdcb` | `mcp_only` | `3a3abaff72a8e6382e4c362865becba069e4ecfc` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 10855 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 10871 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `2ad10a11d826ecba5bd252edf844bc3a6d59a7b0bdc20a82c0f83fbd807e8b01`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
