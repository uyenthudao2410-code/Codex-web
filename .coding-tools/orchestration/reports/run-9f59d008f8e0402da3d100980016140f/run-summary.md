# Orchestration Run Summary

- Run: `9f59d008f8e0402da3d100980016140f`
- Task: `27ebc28263c544afbfdee8fe1f94d4b3`
- Objective: Eliminate the three currently known canonical P4 strict diagnostics without weakening the gate or changing benchmark fixtures to hide failures: M01 exact duplicate support must not inflate promotion support or change promotion decisions; G03 source/epoch proxy must not validate without cross-source generalization; T02 recurrent middle drift must be detected rather than missed by a single latest-third holdout. Preserve unknown-not-zero, familywise confidence semantics, causal-solution repair labeling, synthetic/benchmark non-promotion, p5_automatic_start=false, automatic_policy_activation=false, and all unrelated WIP. Use the existing strict multilayer/research-stress tests as the oracle. No commit/push/restart/deploy.
- Status: **accepted**
- Started: `2026-08-20T03:33:43.119Z`
- Finished: `2026-08-20T03:42:21.858Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `348223a98ced40c1a18c0f80d7360ba8` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | replanned |
| 2 | `b399546ed3af44e9902302ba01ecddf2` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4f3819a5af684ff1b7768b0ffbbbfd2b | b399546ed3af44e9902302ba01ecddf2 | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | 32778273947fda772dd3eb40234d547a174f39b747d58e8277f8e71ecdeec6c5 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 22301 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 22326 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 22320 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `7419b2cfb5ddfcf25a208b90d7a94109428b4c9165a1b9890dc3fdfc81f6f51d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
