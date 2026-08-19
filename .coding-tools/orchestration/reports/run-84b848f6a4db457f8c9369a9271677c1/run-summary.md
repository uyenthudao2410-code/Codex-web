# Orchestration Run Summary

- Run: `84b848f6a4db457f8c9369a9271677c1`
- Task: `c013b686888a44eb9426c99fe8dbaba3`
- Objective: Audit the canonical P4 Solution Economics Shadow gate immediately after accepted representative run a6d4e401e3514ffea5d061854697f3d2. Do not mutate product source or open P5. Treat .coding-tools/orchestration/ledger.sqlite3 as the authoritative causal source. Locate and run the maintained P4 readiness/solution-economics reporter from the correct Coding Tools MCP component working directory. Report: representative terminal sample count, repaired vs nonrepaired counts, each predictor's leave-one-out Brier gain and Bonferroni-adjusted Wilson separation status, validated_signals, p4_gate.can_answer_which_signals_predict_repair, automatic_policy_activation, and p5_automatic_start. Also verify the live smart-v3 contract remains exactly 8 public tools with contract SHA bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70. This is read-only audit evidence and must not be enrolled as a representative shadow sample.
- Status: **aborted**
- Started: `2026-08-18T21:41:52.700Z`
- Finished: `2026-08-18T21:43:54.758Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2579c9c1250b41d2b112ab9bc9f31846` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | replanned |
| 2 | `290c6d9c9a0e40aabdc74e8427ca9f78` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 18249 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 18253 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `81a542487582bcc389e90ca5aa6880cec30cadcde353d9e066694e62dbe09ddf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
