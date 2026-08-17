# Orchestration Run Summary

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Task: `0659f2cbf3214fd4a29b0d6d55605bfc`
- Objective: Finish the remaining compute-first/server-first measurement and evaluation hardening on the isolated worktree only. Preserve current routing authority and production Recovery/installer behavior. Diagnose current code first and identify the smallest coherent implementation that makes local-first versus server-first compute placement genuinely measurable without fake tags: (1) keep compute placement distinct from model-route evaluation, (2) provide an enforceable study-only placement choice or equivalent exact policy identity so a run tagged local-first cannot silently execute server-first and vice versa, without changing the default server-first production policy, (3) persist content-free actual placement decision/execution/fallback evidence with reason/provenance and exact source/environment identity, (4) support delayed controller economics and quality/observation correlation using existing ledger/task_control contracts rather than inventing duplicate telemetry, (5) add a fail-closed paired compute-placement evaluator with quality floor, TTA/total-cost completeness, Pareto/regret projection, representative-only evidence, and automatic_activation=false, (6) preserve unknown cost as unknown, exclude benchmark/synthetic/fault/recovery acceptance rows, and do not claim counterfactual regret from a single run, (7) keep host turn/run/wave binding intact, (8) correct any runtime telemetry field that falsely says shadow-only if live dispatch is actually enabled, but only if current contract evidence proves it is semantically wrong. Add focused tests and update maintained current-state/measurement documentation only if public/operational behavior changes. Do not touch resources/recovery-supervisor, Recovery tests, installer/package surfaces, external Windows state, or main checkout. Do not commit, push, tag, release, restart runtime, or edit volatile .coding-tools evidence. Worktree: .git/compute-placement-evaluation, branch automation/compute-placement-evaluation-20260817, expected base acaa3582052ab6836ade7b55bd1ff2178ebc5117.
- Status: **accepted**
- Started: `2026-08-17T08:52:29.015Z`
- Finished: `2026-08-17T09:02:02.567Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **5**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `8efabd17eb844e448a54bb6fd80e4029` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 2 | `7b30871d5c9349418e8c7f80ec0d7083` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 3 | `b528b4bd2ced4fefa171b976d9c13321` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 4 | `1641e600a27a4e6db226516c84db3688` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 5 | `3f806415a330408d9cafac264c788337` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 6 | `bbfabb23f96d43ebb6d55e159847b0ac` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2381e14e36c248caa363c326be61d126 | bbfabb23f96d43ebb6d55e159847b0ac | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 151d06aee9c8b009f3bed55257106ef6d782183b03ad5bee80ccfff865efaf19 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12844 | `deterministic` | `deterministic` | explicit_request |
| 12863 | `deterministic` | `deterministic` | explicit_request |
| 12902 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 12956 | `deterministic` | `deterministic` | explicit_request |
| 12988 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 12836 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 12855 | `CHECK_FAILED` | `PROVING` |  |
| 12867 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 12913 | `CHECK_FAILED` | `PROVING` |  |
| 12980 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
