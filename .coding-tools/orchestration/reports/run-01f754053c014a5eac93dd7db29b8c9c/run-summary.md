# Orchestration Run Summary

- Run: `01f754053c014a5eac93dd7db29b8c9c`
- Task: `024a1ec9d83c447c9b760e8a3592fb65`
- Objective: Fix bounded Mini/Luna candidate packet localization for deep symbols in large files. Preserve the 14k source-evidence budget: reserve a bounded portion for unique query-centered snippets read around search match line numbers on allowed_paths, count snippet content against the same remaining budget, then fill remaining budget with existing head-of-file slices. Keep existing compact search metadata. Ignore invalid/out-of-scope matches fail-closed. Add a focused regression test where the target symbol is after line 2000 so prepare_coding_context truncates the file head but the candidate packet still contains an exact local snippet around the deep match. Do not change routing thresholds or candidate write authority.
- Status: **accepted**
- Started: `2026-08-14T04:04:37.273Z`
- Finished: `2026-08-14T04:06:58.037Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `fc954bb3cf6e4040ae8e708e0fdcb0da` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `3f8ea6a03cd545f485dcc1f44d7bbf84` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 3 | `5ca5392b1ce44462a8a1a1d93043c579` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 0b4ce073a4a74da7a23f061f08a947b5 | 5ca5392b1ce44462a8a1a1d93043c579 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | fe80ea00804b96d3167a7c292f5e0adbbde30f66677c62b5792665f1c7d2ba64 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 835 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 848 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 858 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 843 | `SOL_REJECTED` | `ACCEPTING` | Final efficiency review found one boundedness improvement before acceptance: the 6k snippet character budget limits payload size but very short snippets could still trigger up to 18 deep read_file scans (6 queries x 3 matches). Add an explicit maximum of 4 unique query-centered snippets so candidate packet I/O is deterministically bounded while preserving the new deep-symbol evidence behavior. |
| 852 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `fad8716b68d62239b84b555f291231b4318c5e2368e54533089cd76a9c151784`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
