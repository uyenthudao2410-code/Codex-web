# Orchestration Run Summary

- Run: `ad857b3089b94b8e9eeebdea467538e5`
- Task: `fc67d5a7b4b44cb3a0aea09161ab93e6`
- Objective: Triển khai hệ thống canonical token accounting chính xác và ChatWeb exact usage telemetry. Thiết kế đã chốt: OpenAI/DeepSeek cache là subset input và reasoning subset output; Gemini thoughts có thể cộng riêng; Anthropic cache read/create tách khỏi uncached input. Canonical UsageEvent phải chứa input_total_tokens, input_cached_tokens, input_uncached_tokens, output_total_tokens, output_reasoning_tokens, output_nonreasoning_tokens, total_tokens và accounting profile/provenance; legacy fields giữ tương thích. Ledger phải aggregate toàn bộ UsageEvent trong 7 ngày (không limit=8), recent events vẫn bounded. Dashboard KPI/trend/model chỉ dùng canonical measured analytics; model-visible bytes chỉ là estimate riêng. ChatWeb/controller exact usage chỉ nhận từ trusted client/host report (qua MCP custom _meta hoặc hub telemetry), dedupe bằng turn identity; thiếu telemetry thì unknown, không tokenizer/DOM giả làm exact. Thêm focused tests. Không commit/push/restart, bảo toàn unrelated worktree changes.
- Status: **accepted**
- Started: `2026-08-19T08:22:02.409Z`
- Finished: `2026-08-19T08:37:02.977Z`

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
| 1 | `71f7fa1d6c5d46c380d9ccd88207b95f` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| aba148bca26d478e85f963de58583508 | 71f7fa1d6c5d46c380d9ccd88207b95f | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | a527c2369a0ecf9a6294ad7add9c02505fb26938b67566f5254e8b7d5a213d6c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 20930 | `auto` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `3c93981592f3bff47c48bf6583997694fb8f2b98a7ddadf60d76530cdb4b467a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
