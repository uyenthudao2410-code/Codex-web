# Orchestration Run Summary

- Run: `1e82559fa91a498ab0cd92c3d33522d7`
- Task: `66c8d5e4480a419a8f464cd3cf0cfde1`
- Objective: Fix the packaged Recovery Supervisor UTF-8 manifest decoding defect proven by the win-unpacked acceptance probe. Write-JsonAtomic emits UTF-8 without BOM, so Read-BoundedJson must decode explicitly as UTF-8 instead of relying on Windows PowerShell 5.1 Get-Content default encoding. Add a focused Windows regression using a packaged-mode manifest whose executable/app_root contain the actual Vietnamese-style Unicode product path; prove Action Once parses it and remains degraded rather than falsely reporting executable missing. Preserve all manifest validation, fail-closed spawn/hash rules, and source behavior otherwise.
- Status: **accepted**
- Started: `2026-08-17T07:20:14.676Z`
- Finished: `2026-08-17T07:20:43.746Z`

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
| 1 | `4b8f4d87edc941bfa8ba65aa81c8d6c5` | `mcp_only` | `f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 045033950b044d32b85c07ab283c69a9 | 4b8f4d87edc941bfa8ba65aa81c8d6c5 | accepted | f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1 | 3cdc8e741df17e49387e733a769bf57dfaa52b945a4ef631d41b945579afd551 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11934 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `7ea5ab86f411b851d8b10d7bb728440b3a4d3ab0674aa631de33d31bdf2896b2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
