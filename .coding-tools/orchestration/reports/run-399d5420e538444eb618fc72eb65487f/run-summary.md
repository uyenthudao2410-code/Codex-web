# Orchestration Run Summary

- Run: `399d5420e538444eb618fc72eb65487f`
- Task: `3fdae1a0027b42c88b1420cd0d13e4e1`
- Objective: S8 gate audit for W8 Computer Use and W12 reverse relay/device lease. Determine current source-present behavior, security/authority boundaries, and exact missing invariants against the technical plan. W8 production gate: W7 minimum security contract plus policy levels observe_only / interactive_low_risk / sensitive_action_requires_approval / blocked; bounded screenshot/snapshot, click, keyboard, scroll, display/window selection, clipboard opt-in; credential dialogs, destructive OS controls, financial/payment flows, and secret-bearing clipboard sensitive. W12 gate: device identity + project grant + runtime instance + expiring connection lease + reconnect token/epoch; stale connections lose authority, reconnect cannot duplicate jobs, revocation/project boundary explicit. W7 and W10 are accepted. Audit existing Electron/Recovery/tunnel/runtime/permission/capability code and tests; identify whether a concrete W12 use case exists. Do not mutate source or Markdown. Do not add tools. No commit/push/restart/deploy/release.
- Status: **accepted**
- Started: `2026-08-21T02:50:49.875Z`
- Finished: `2026-08-21T02:53:22.200Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `57ad4027c28a46eda1ca6fb9e48c9f12` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `89865d70f047498f85acc318637f32aa` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| db4a1ec36c404ea0a152d7eaff49ba2f | 89865d70f047498f85acc318637f32aa | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | a6c4b7e4f1ccf75a3dc28add00f4a3dcb17e88595643811197c6c6aec89ccae8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25561 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 25555 | `CONTRACT_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `cb202d0313ee5fd9ba7c319839d570ca55139646630472dde751585800baa6d3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
