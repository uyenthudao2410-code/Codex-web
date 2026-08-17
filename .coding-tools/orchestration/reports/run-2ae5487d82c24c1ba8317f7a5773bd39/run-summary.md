# Orchestration Run Summary

- Run: `2ae5487d82c24c1ba8317f7a5773bd39`
- Task: `f941ae21e999480290213e858ede0a49`
- Objective: Complete final pre-P3 intention-to-treat paired-analysis readiness without starting P3 treatment. Extend paired_policy_evaluation output so all explicit representative comparable pairs, regardless of terminal status, report symmetric baseline/candidate acceptance rates, first-pass acceptance rates, and repair rates. Keep TTAR conditional on both accepted. Add a regression where baseline is accepted and SERVER_FIRST_DETERMINISTIC_V1 candidate is aborted with a replan, proving the aborted candidate remains in pair_count and yields candidate_acceptance_rate=0, candidate_first_pass_rate=0, candidate_repair_rate=1 instead of being survivor-filtered. Preserve exact pair identity, unknown cost semantics, automatic_activation=false, and existing ledger/public MCP semantics.
- Status: **accepted**
- Started: `2026-08-17T20:00:33.805Z`
- Finished: `2026-08-17T20:04:22.396Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a6de1f5715684d8dbfc2d1b403a52fc7` | `mcp_only` | `bc07e240740726d9a5ddbd590e01568344a92440` | replanned |
| 2 | `942e5dcd2efb42ea874856fe0e466572` | `mcp_only` | `bc07e240740726d9a5ddbd590e01568344a92440` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7c5207ad789d4a0f95fd016848737a1f | 942e5dcd2efb42ea874856fe0e466572 | accepted | bc07e240740726d9a5ddbd590e01568344a92440 | 00fcbe372f23cc3191b278c3b132a6eb094eb7fda3149b9f8179a22a09f8b76b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15719 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 15752 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 15745 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `286be33bc51845409aa2651b2d40993524be52729f737d72d3c1a15045089563`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
