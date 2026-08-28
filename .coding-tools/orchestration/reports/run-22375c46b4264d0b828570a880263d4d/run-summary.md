# Orchestration Run Summary

- Run: `22375c46b4264d0b828570a880263d4d`
- Task: `1674d4a6319c4b2fba0c73dec9fd0e2c`
- Objective: Fix Coding Tools MCP multi-workspace execution so a task bound to an extra authorized root consistently uses that resolved task workspace for patch preflight/apply, verification workdir, git diff/proof identity and acceptance while the primary UI workspace remains unchanged. Preserve fail-closed authorization and workspace identity boundaries.
- Status: **accepted**
- Started: `2026-08-28T10:06:51.383Z`
- Finished: `2026-08-28T10:28:54.080Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `447b9c2bbe8d44f280f34d5537febf9d` | 1 | `run_initial_objective` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 2 | `6ea8325a61ca4b20bf44a75ca302bf4f` | 2 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 3 | `bdb189dec0c24a46b67a12eac57acb59` | 3 | `replan_request` | `mcp_only` | `148de18795787e820ef1bc51d0f2591052d24238` | replanned |
| 4 | `c1fb4f4451bb4cde945b9f156368ce98` | 4 | `replan_request` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | replanned |
| 5 | `8fb0946c6c7040efabd9562fb4209efe` | 5 | `replan_request` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| dc6a6d8fc33d4933894eabb2058ec6a6 | 8fb0946c6c7040efabd9562fb4209efe | accepted | 2cc0eefc7d881827ef44e4d1584d84bbd9e494b6 | 4e0d8b4e9d2dbd5f0c06193f5a1de856e8adbd9ce12549d9b830b776812c1a95 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32023 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32057 | `deterministic` | `deterministic` | explicit_request |
| 32081 | `deterministic` | `deterministic` | explicit_request |
| 32132 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32154 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32044 | `CHECK_FAILED` | `PROVING` |  |
| 32074 | `CHECK_FAILED` | `PROVING` |  |
| 32095 | `CHECK_FAILED` | `PROVING` |  |
| 32147 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `131`
- Chain head: `aeca16276d3a7d3a11d67dd357846421e95283bd0963f7175aefcc239e4640bf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
