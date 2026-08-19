# Orchestration Run Summary

- Run: `482171d427dc4fdfb3c9b3e28cc42552`
- Task: `505187b2bf284aa1a1b3e552f1d59897`
- Objective: Implement token-accounting wave 2 only: canonical non-overlapping pricing; durable exact 7-day UsageEvent analytics across all runs with hourly UTC/by actor/provider/model/rolling 5m; strict conflicting usage_id rejection; provider economics excludes controller actor; expose analytics in control orchestration snapshot. Preserve accepted UsageEvent v2 and all unrelated work. No ChatWeb ingress/dashboard yet. No commit/push/restart.
- Status: **accepted**
- Started: `2026-08-19T08:58:49.168Z`
- Finished: `2026-08-19T09:05:06.438Z`

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
| 1 | `e870fc6ffc164e26a08e49a9b38d94c3` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 2 | `8d9153fb9410486bb9370b6bf25cb85d` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 01003918da5a433cab8f7458f0ecef65 | 8d9153fb9410486bb9370b6bf25cb85d | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | d1f2dc1265121ea20619a8e4d83c9a12fec53760ffe663bbc976e0ec722a6db3 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 21060 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21080 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 21066 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `65`
- Chain head: `e9c5b9abd9c739f7042d273b2ccfe1baf4cf104b2042c4886645fecf71d6e28b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
