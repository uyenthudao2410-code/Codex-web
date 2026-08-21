# Orchestration Run Summary

- Run: `6ff3fbb8c1524273941378ea4628f2aa`
- Task: `971ce094834c441dbc40b6b438ed0b5d`
- Objective: Build and verify the final local NSIS release-candidate artifact from the already accepted source fingerprint. Run the complete dist script, re-run packaged Recovery smoke against the final win-unpacked output, verify git diff/source-root hygiene, and print content-free installer SHA-256, size, and mtime. Local verification only: no release/publish/deploy, no commit/push, no live runtime restart, no provider dispatch.
- Status: **accepted**
- Started: `2026-08-21T04:27:37.271Z`
- Finished: `2026-08-21T04:37:33.145Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `866b6fd12cc245998a5f3f80719cbb7d` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `fbfedf3da6c14438b349131d215f2c07` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 3 | `875172194c91453e9a82d92c7cd48fa1` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 284eb5514aef44dab57ec12326ef9635 | 875172194c91453e9a82d92c7cd48fa1 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 41a58e43ce4edbdbdf0addf9bd30c6ce44f60496fed6d035c6e20825fbc1bc9d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25885 | `deterministic` | `deterministic` | explicit_request |
| 25928 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 25947 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 25918 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 25940 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `c279f696ad227144f73aa3f55d5e2582310ef2d2b424f06a2cdf03a5c8d3ff25`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
