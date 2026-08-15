# Orchestration Run Summary

- Run: `7ce1f4c4d5ea4fa0a4dad8bbe6b1dec2`
- Task: `89d00b9c23b84ee7bef06eac84b43ccd`
- Objective: P1.D: add an operational evaluation-plane reporter that summarizes the independent Electron host-visible journal, reports p50/p90 user-visible-to-first-assistant-visible spans without calling them model latency, reports ledger critical-path DAG for an explicit run when requested, and marks host-to-run correlation unlinked unless an explicitly correlated host observation span with trace/turn identity exists in that run. Also update exact smart-v3 contract SHA expectations to the new deterministic source contract after task_control observation was added. Add focused tests.
- Status: **accepted**
- Started: `2026-08-15T08:13:29.737Z`
- Finished: `2026-08-15T08:14:02.556Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `d8ce0b55ced745b5941ba189685467fa` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c7bc4fafb6ae45d5b3b4190bc443be0d | d8ce0b55ced745b5941ba189685467fa | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 8832362d35626ce5763d9a27d15701b5355fc1d9ed55542cab316fee73425b22 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4943 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `cbe3bae5f32f7dc049a15018e108ff469faa18007f8fbad13e38452bbf0e0580`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
