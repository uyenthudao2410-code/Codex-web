# Orchestration Run Summary

- Run: `bcf534336c78473a8aa3a577b0fbc1ac`
- Task: `3d76b827c18844a6b2534564eca1f1cd`
- Objective: Continue P0 proof only. Source patches are already applied. Re-run the focused Python tests from the Coding Tools MCP package directory; the previous failure was test-runner cwd/import setup, not a code assertion. Preserve the already-passed Node packaging proof and diff-check evidence. No new source changes unless a real test assertion fails.
- Status: **active**
- Started: `2026-08-15T00:03:58.426Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9b69917c875f451baa0186830db585d5` | `mcp_only` | `8581b8331e83cc600c2b813629875639e48a8245` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3595 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5573 | `SOL_REJECTED` | `ACCEPTING` | Stale unrelated P0 acceptance lineage: audited proof is green for historical base_head 8581b833... and worktree fingerprint 512437..., while the current P2/P3 checkout is on a different base/worktree. Reject rather than falsely accepting evidence that does not bind to the current source state. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `c593ddb6a9e380565d91f33c14df1ca9644e5f850301c42ace24737ea18507ee`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
