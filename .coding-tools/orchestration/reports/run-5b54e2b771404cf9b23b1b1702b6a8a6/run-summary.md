# Orchestration Run Summary

- Run: `5b54e2b771404cf9b23b1b1702b6a8a6`
- Task: `f6c4ff3e10bf4b1abca90b994c9c0308`
- Objective: Read only the exact JSON output contract of reconcile_exact_stale_run.py and its return value from reconcile_exact_stale_run so the Recovery Host validator can be exact. Do not execute reconciliation and do not modify anything.
- Status: **accepted**
- Started: `2026-09-07T02:51:43.392Z`
- Finished: `2026-09-07T02:52:10.476Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `1801212072054bce81cdd03ff7f93032` | 1 | `run_initial_objective` | `mcp_only` | `9255f94c9beff33f8c6c53d6745a08968f5a12bb` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6c0cdd8fea4a41c6915ae77bf0fec8b1 | 1801212072054bce81cdd03ff7f93032 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | b9e4a7bd455698528661adff1005bcca191c206c845eb1f0c85a4c574688a33c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 42955 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `5edbb3b8b02850c2dd4d9259495b09dca56e0298b82b6b9d3e41c409a0f1a162`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
