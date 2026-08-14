# Orchestration Run Summary

- Run: `0c2dc9997e3c41af9bec10734a3a323b`
- Task: `f31892ddcc4048b7954c7cd9e8a7ac30`
- Objective: Wave B: hoàn thiện measurement truth trong orchestration ledger. run_phase_timing phải trả terminal TTA, observed/unattributed time, coverage và 0.90/0.95 gates; accepted_result_economics phải dùng projection này và thêm provider timing như overlapping evidence, không cộng vào EOCL observed_ms. Bổ sung focused tests deterministic. Không đổi routing/authority.
- Status: **accepted**
- Started: `2026-08-14T16:16:46.540Z`
- Finished: `2026-08-14T16:18:12.075Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `8c9aaf6366c5478bba44049282d77040` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | replanned |
| 2 | `600e545955984510b18443cb7f12ba27` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | replanned |
| 3 | `5d6a605e5ec0440487e13c59262dfb98` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a5ed35ca8bb6459ba773e8d45db78ca8 | 5d6a605e5ec0440487e13c59262dfb98 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2722 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 2732 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 2742 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2726 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 2736 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `545cedfe84b581e0facb2f37486d572ef995704e00219a002265bbd432ac61a6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
