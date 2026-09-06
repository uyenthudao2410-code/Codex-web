# Orchestration Run Summary

- Run: `2498e44384ec4f8cac2b1a70d0957349`
- Task: `f435d9a8bf59415da015cd89ae8faefb`
- Objective: Recovery integration preflight correction: apply only the five intended stashed source/test changes, then make the closed-activation compatibility bootstrap accept only exact managed-tunnel-attested ChatWeb authority. Preserve the pulled recycled-PID repair and all existing READY/workspace fail-closed gates.
- Status: **active**
- Started: `2026-09-06T04:57:32.481Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f58a41cf2d2a4ff79209eda3e43b83aa` | 1 | `run_initial_objective` | `mcp_only` | `573b6ff5a5ff2509288c9656e18fd375f1ab32d3` | replanned |
| 2 | `8d0547393c034f8f9da4366bc98dc38b` | 2 | `replan_request` | `mcp_only` | `573b6ff5a5ff2509288c9656e18fd375f1ab32d3` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41204 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 41266 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41259 | `SOL_REJECTED` | `ACCEPTING` | ACCEPTANCE_PROOF_REQUIRED: post-write Node 56/56, Python 48/48, and diff-check all passed, but they were terminal-managed evidence rather than canonical EOCL proof records. Preserve the exact current bytes, REPLAN under the same RUN, adopt those bytes by SHA-256, and rerun the smallest sufficient verification through agent_workflow so acceptance has content-addressed proof authority. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `58`
- Chain head: `77c05b90dbc9fd55ec1d9a24a92797f6b81c11db4fe76df634ec0f7d680442b6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
