# Orchestration Run Summary

- Run: `d9c08fc64fe34d17ad13915bfc8cc778`
- Task: `0e1078add721484a9b8635adb9ed8741`
- Objective: Resume and complete the accepted-code automatic activation work after the MCP reconnect. Inspect the already-present Recovery Host auto-activation controller and related wiring, then prepare the minimal integration delta that changes trust from a single-wave modified_files gate to a running-baseline plus canonical accepted SHA-256 receipt union. Preserve unrelated dirty Python/Rust/docs/.coding-tools work. Future activation must remain Recovery Host-owned, fail closed on unaccepted byte drift, avoid source watchers/restart-all/arbitrary paths, and use existing Safe Code Activation component order. Do not mutate in this prepare phase.
- Status: **accepted**
- Started: `2026-08-16T06:04:54.670Z`
- Finished: `2026-08-16T06:14:48.842Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3d21a45d99074a4d8e63e16a9fc7ed7b` | `mcp_only` | `597170860118a847b7e8a6f06903c37da8432d82` | replanned |
| 2 | `0466900a5f9940d591518328c057d519` | `mcp_only` | `597170860118a847b7e8a6f06903c37da8432d82` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e4f29a39033446859439dd70ebaa91da | 0466900a5f9940d591518328c057d519 | accepted | 597170860118a847b7e8a6f06903c37da8432d82 | b399f7fdf71a6d2b747a2390a14ebc24ef2e1a606d396de05ddfea842270a6c2 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 6026 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 6042 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 6036 | `SOL_REJECTED` | `ACCEPTING` | Source V2 parses, but the source-only wave has no acceptance proof and the existing V1 fixtures fail because they do not contain canonical accepted_files receipts. Keep the applied source changes, replan the same run to update deterministic receipt/running-revision oracles and prove the complete contract. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `73`
- Chain head: `f264f4df913169de534f8892f03b91141ab319567ccd6eba5a07be54baec9b1d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
