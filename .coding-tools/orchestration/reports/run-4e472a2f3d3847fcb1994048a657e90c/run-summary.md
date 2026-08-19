# Orchestration Run Summary

- Run: `4e472a2f3d3847fcb1994048a657e90c`
- Task: `cd351d3ebae242d1b7bc195b8834c9b7`
- Objective: Apply the already-enrolled realtime-performance fix only. Use exact rolling 5-minute provider usage samples for TPM and exact rolling 5-minute recent performance records for average latency. Add explicit freshness/no-data labels. Remove stale hourly/daily/all-history fallbacks and the undefined compactNumber call. Preserve 3s polling, 10s performance throttle, 4s orchestration throttle, backend/public MCP surface, fleet-table behavior, and unrelated work.
- Status: **aborted**
- Started: `2026-08-19T06:09:55.007Z`
- Finished: `2026-08-19T06:10:42.722Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f2f89afa8a624937bd96092ca13034ee` | `mcp_only` | `359a5f231e1950e8d97303e0d2b798984c145fe6` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `4`
- Chain head: `ac00eb12c9d6850fb2cd7dfb7a6173107945cf24724dd9e30c9d70f16a074eab`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
