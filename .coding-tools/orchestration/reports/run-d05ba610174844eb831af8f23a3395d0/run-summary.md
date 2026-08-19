# Orchestration Run Summary

- Run: `d05ba610174844eb831af8f23a3395d0`
- Task: `20be1820f7124d00a503fad5fefac73e`
- Objective: Fix the genuine exact-fit tracked-diff byte-budget bug in crates/webcodex-workspace/src/project_context.rs. Current worktree_sha256 marks worktree partial whenever remaining becomes zero after bounded_git_output, even when a repository with HEAD has a single complete git diff whose byte length exactly equals max_tracked_diff_bytes. Preserve fail-closed partial classification when output actually truncates/exceeds the budget and when another required diff slice cannot be read. Add the smallest same-module unit regression proving an exact-fit complete HEAD diff remains complete, while existing large_tracked_diff_is_partial_instead_of_read_without_limit continues covering true overflow. Do not touch unrelated files, do not commit/push, do not restart, and do not manufacture a replan. This is a genuine representative P4 bugfix sample.
- Status: **accepted**
- Started: `2026-08-18T15:43:10.646Z`
- Finished: `2026-08-18T15:46:12.792Z`

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
| 1 | `0337a944db5e48aca8238be15435e7e5` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b7eb125a94224c3497a9863bbd4266b7 | 0337a944db5e48aca8238be15435e7e5 | accepted | b7af2598297870e816dd131b0f73e0f77d7608d5 | cf1dc19b1f5c4b14967b5f69469d2f827410f0e2fd8b7d29a420cfce168085bc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 18062 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `5198f54cff4c17962f750940a1925846d8762a88ca1b7eb1f006f56adb8d786d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
