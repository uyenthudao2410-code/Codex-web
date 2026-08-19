# Orchestration Run Summary

- Run: `210ff0f13f2948b68fb57904243caffa`
- Task: `a055406327fe49ffaf0dca38f1bbe6d9`
- Objective: Wave 2: sau canonical UsageEvent đã accepted, bổ sung pricing theo canonical fields để không double-count reasoning/cache; thêm ledger analytics 7 ngày quét toàn bộ UsageEvent trong window, exact hourly + rolling 5m + by-model + provenance/cost; recent_usage_events(limit=8) chỉ giữ debug; provider_economics phải loại controller events. Thêm focused tests mới, bảo toàn mọi thay đổi unrelated, không commit/push/restart.
- Status: **aborted**
- Started: `2026-08-19T08:37:43.127Z`
- Finished: `2026-08-19T08:40:40.461Z`

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
| 1 | `837cf4087f5b49478ed6c804c405ea5e` | `auto` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | aborted |

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
- Events checked: `14`
- Chain head: `a39f9ed34a010b8efa1eca3cdb862642af6fc626dd7b7479faff2bc4d2585461`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
