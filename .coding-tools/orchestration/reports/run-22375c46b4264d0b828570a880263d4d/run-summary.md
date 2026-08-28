# Orchestration Run Summary

- Run: `22375c46b4264d0b828570a880263d4d`
- Task: `1674d4a6319c4b2fba0c73dec9fd0e2c`
- Objective: Fix Coding Tools MCP multi-workspace execution so a task bound to an extra authorized root consistently uses that resolved task workspace for patch preflight/apply, verification workdir, git diff/proof identity and acceptance while the primary UI workspace remains unchanged. Preserve fail-closed authorization and workspace identity boundaries.
- Status: **active**
- Started: `2026-08-28T10:06:51.383Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `447b9c2bbe8d44f280f34d5537febf9d` | 1 | `run_initial_objective` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 2 | `6ea8325a61ca4b20bf44a75ca302bf4f` | 2 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 3 | `bdb189dec0c24a46b67a12eac57acb59` | 3 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32023 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32057 | `deterministic` | `deterministic` | explicit_request |
| 32081 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32044 | `CHECK_FAILED` | `PROVING` |  |
| 32074 | `CHECK_FAILED` | `PROVING` |  |
| 32095 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `596ef3976a8b3566ddb611a72f61c07740493cdf503153418f2037dc31c600e6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
