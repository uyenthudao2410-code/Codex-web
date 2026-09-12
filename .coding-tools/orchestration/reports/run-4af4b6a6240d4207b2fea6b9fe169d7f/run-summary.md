# Orchestration Run Summary

- Run: `4af4b6a6240d4207b2fea6b9fe169d7f`
- Task: `de84e7a1846c40589d8755f7d93cf8e4`
- Objective: Restore Control Center tabs: manager window must load index.html, token window stays token-dashboard.html
- Status: **aborted**
- Started: `2026-09-08T06:58:27.384Z`
- Finished: `2026-09-09T07:43:47.473Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `bbb9c934332f47ccbf926e486fdf90fb` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43775 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45213 | `SOL_REJECTED` | `ACCEPTING` | Historical non-Problem wave is still ACCEPTING from 2026-09-08, has no durable file receipts, no live owner/job/lease, and its proof source fingerprint 853ea5a6700669f12af2659613e6bcd636e228e3872ce9d33d613dec764c63f9 does not match the current worktree fingerprint c6f9071869d4882401a598b4463ab6c5b574382ead7d293a98a6e8830283b931. Reject rather than falsely accept stale proof. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `65fcc5190cb3675ffefe649b76bf6de2120a387f34ec1b6719f1ffed6b0378c2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
