# Orchestration Run Summary

- Run: `9c3444ce503f435e9aa5ba386a80c8cf`
- Task: `b56ec8b1a9864053ba23b2eba3c2d019`
- Objective: Wave B2: accepted_result_economics dùng run_phase_timing làm nguồn TTA coverage duy nhất, thêm provider timing delegation metadata dưới evidence overlapping, và bổ sung deterministic tests cho coverage gate + provider timing. Không cộng provider timing vào EOCL observed_ms.
- Status: **accepted**
- Started: `2026-08-14T16:18:44.949Z`
- Finished: `2026-08-14T16:19:13.717Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `b0dea52581524f2994b0bcef31e26182` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2ddf3ea7e8aa4e518ff248023df2ce57 | b0dea52581524f2994b0bcef31e26182 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2753 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `e1ea892b06173312c8f1f65eab6c8312035805089612f6b2149f6683f39d85ea`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
