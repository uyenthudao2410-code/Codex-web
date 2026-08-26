# Orchestration Run Summary

- Run: `0ca7f60e56544df9aadb9fb89f7df48f`
- Task: `2a05bb35c83842fe961dbc56587b4140`
- Objective: Strengthen the stateless exact-run continuation regression so it proves a run whose controller has been explicitly transferred to another active principal is not auto-recovered into the old ChatWeb application context. This is a test-only hardening change; do not change production behavior.
- Status: **aborted**
- Started: `2026-08-25T15:02:42.711Z`
- Finished: `2026-08-26T08:21:40.360Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `e3f93399444a47ed9fec9042b83bfce6` | 1 | `run_initial_objective` | `mcp_only` | `0557afa6c3aa3e02c2664d312b860973f28d3fc5` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 29713 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `b76dffb085cf733a1593e774264c461dc372476a72640c3a06a5f2647b083419`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
