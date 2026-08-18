# Orchestration Run Summary

- Run: `80e86f38194f4df0835ee8138e272ab9`
- Task: `8d8453bdb66d470a9a2336e225b7cfd6`
- Objective: Commit and push the fully accepted PR #17 repair to origin/main using the repository's unanimous recent author identity only as a commit-local override. Include the two repaired tests, removal of nested private runtime state, byte-identical migrated ledger, and the complete current repository-root .coding-tools evidence. Run the delivery guard around each evidence snapshot and fail closed if origin/main is not exactly the current base before committing.
- Status: **aborted**
- Started: `2026-08-18T08:52:44.086Z`
- Finished: `2026-08-18T08:54:11.136Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1305634ba73c4034aa6f167a62c28721` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 2 | `f926cd35cae2490387ffbdd8f3f74fb9` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16748 | `deterministic` | `deterministic` | explicit_request |
| 16782 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16774 | `CHECK_FAILED` | `PROVING` |  |
| 16808 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `10e92a81fdd1229013c340164ced68771f57892e1cc2f6bbc6f307f477f0c484`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
