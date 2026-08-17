# Orchestration Run Summary

- Run: `d6a4147e0069484d83d1ce36c94be629`
- Task: `03ff314323844e038d00974a88578ef4`
- Objective: Read-only authoritative mapping for remaining P0.3 F1/F7/F8 on the current worktree. F1 requirement: killing/exiting the real UI/Electron client must not destroy independent Recovery Host ownership, and a replacement UI/client must reattach without replacing healthy Recovery Host/MCP/Tunnel ownership. F7 requirement: stale Recovery Host lock/ownership metadata from a dead owner must be safely reclaimed/recovered without adopting or killing unrelated live processes. F8 requirement: a live but unhealthy/foreign/mismatched owner/listener must fail closed rather than being adopted or killed. Inspect the current production code and exact tests, identify existing test names/assertions that satisfy each requirement, and identify any precise missing assertion or real product gap. Also locate the authoritative F1-F9 section in docs/PRODUCTION_CLOSURE_ROLLOUT.md. Do not mutate files, restart live production processes, or touch Operator Control Panel/UI source.
- Status: **accepted**
- Started: `2026-08-17T11:16:28.902Z`
- Finished: `2026-08-17T11:20:22.869Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `7705c4274faa44219a19a4fafc09f32b` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `d6c0c31020474dbfb950b6819c3936ca` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4ae5b2b301ea4cd0a02a56e71e1f18f3 | d6c0c31020474dbfb950b6819c3936ca | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 4e118fde2a5e808e814bf5b1d86b1e66c45c5bbd7950c2781b9740b8b4126318 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13746 | `deterministic` | `deterministic` | explicit_request |
| 13768 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13761 | `SOL_REJECTED` | `ACCEPTING` | Reject this wave because it completed verification with modified_files=[] and therefore did not implement the user's requested UI redesign. Start a new deterministic implementation wave after inspecting exact current source. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `53`
- Chain head: `81726c3e445d87997fba72ef4ea76e2bf76744d78f3a63928da96ed6df89f3c7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
