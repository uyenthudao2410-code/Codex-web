# Orchestration Run Summary

- Run: `d455e965665f474f9827a0c511df6049`
- Task: `7b534c38ddc14ad38ea91b696e76b023`
- Objective: Reduce dominant replan/rework causes without changing routing or acceptance policy. Add deterministic caller-patch batch preflight before EOCL run creation so disjoint ambiguous/context-invalid patches fail before any run/write/partial mutation; add bounded candidate line diagnostics for ambiguous hunks; and make agent_workflow/verify_build honor the existing workdir argument for test/build commands. Add focused regressions only. Preserve Smart-v3 tool count, provider gates, EOCL authority, cost-attribution work, and unrelated dirty files. Do not call providers or external review.
- Status: **accepted**
- Started: `2026-08-15T05:25:22.925Z`
- Finished: `2026-08-15T05:28:35.713Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `90875af5740f401b8358b8bfb72c3188` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `2d868a31ea5341d29acf39c486aeae3a` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 81bdd4c30b8543ec9c23d428c9ce15a7 | 2d868a31ea5341d29acf39c486aeae3a | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | d34b326eb4feb623e4d500e4f734f51ccf0ea2c4b904526b103fa877d34bc61e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4423 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 4433 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4427 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `55361231148c6956011b763cf8d41b4f40c3f1b7ce1bda23e41d634608284996`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
