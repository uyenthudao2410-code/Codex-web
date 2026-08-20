# Orchestration Run Summary

- Run: `655e0aa366fe4815997bfd84d8f525e0`
- Task: `358b5bdb93874e9d846a74cc4754177f`
- Objective: Fix only the two known research-stress fixture defects G04_cross_source_stable_signal_recovers and S01_rare_positive_strong_signal_recovers. Do not change canonical validator semantics, readiness thresholds, promotion policy, P5 treatment behavior, or synthetic promotion rules. Preserve the v5 validator behavior that already makes G03/M01/T02 pass. Acceptance: raw run_p4_research_stress_suite.py must become 35/35 PASS with blind_spots=[], multilayer strict must remain 37/37 PASS with canonical non-interference, and canonical readiness before/after the benchmark must remain unchanged. Do not commit, push, restart, or activate treatment in this wave.
- Status: **accepted**
- Started: `2026-08-20T04:27:55.169Z`
- Finished: `2026-08-20T04:32:51.390Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `5f7e7d25c41c42b1879a3c921d483f63` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | replanned |
| 2 | `af1f4a879a7b424589d692a250652bf8` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| bae4a87f663b4371a18229ad405c9c90 | af1f4a879a7b424589d692a250652bf8 | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | 0eaee50f50dfe772eaf9824e62da7493f814eabae2ecaee5ee28c559acf6c087 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 22525 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 22548 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 22542 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `261defdf25750d0535920a99325b36111e5b3a30c65d20ff950f86e6b7dd7a6e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
