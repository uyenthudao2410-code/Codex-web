# Orchestration Run Summary

- Run: `82d3a99b3aac4ae3a76219c0d33a6a2d`
- Task: `d9c63a1fe73140a684c1e930902e4e43`
- Objective: Finish dashboard truthfulness copy for the retained recent trace window. Do not change layout or analytics math. Replace full-day/billing-sounding labels with recent-trace context/evidence labels: model-visible bytes are MEASURED, byte-to-token is ESTIMATED, model usage is MEASURED only when delegation economics supplies numeric counters, and all configured-rate costs are SCENARIO rather than provider billing.
- Status: **accepted**
- Started: `2026-08-14T08:48:24.219Z`
- Finished: `2026-08-14T08:48:47.902Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `363f17b91f4b43669ad590a567dd9a4c` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2f6c808954654faba2685e2e3cef58e4 | 363f17b91f4b43669ad590a567dd9a4c | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | cc145f6720a1b9f0e0f3ebbde4cc8c139ebb71a961b3f4dd59f25990d3700d50 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1660 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `50aece2f44c8b51cf0e9603205a79bdc7f2b00d9632ece60a496281ffa490f2d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
