# Orchestration Run Summary

- Run: `7b52ca1cd8014a2ba411e0e9d7950aea`
- Task: `325ddd35669046448c9f85c42270657f`
- Objective: P1.C: implement a fail-closed controlled replay harness with deterministic seeded counterbalanced AB/BA planning and an explicit opt-in isolated executor. It must never invent tasks, prompts, policies, or synthetic workloads; synthetic provenance is rejected. Execution, when explicitly requested by a future caller, must create a fresh detached git worktree at the exact base HEAD for every trial, run only caller-supplied argv sequentially, record content-free timing/status/output hashes, clean the temporary worktree, and never infer accepted-result quality from exit code. Add a plan-only CLI and focused tests. Do not execute any replay workload in this wave.
- Status: **accepted**
- Started: `2026-08-15T08:12:14.643Z`
- Finished: `2026-08-15T08:12:38.666Z`

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
| 1 | `b80650c55f544d84be4870a1088cbb2c` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c9a52e48abc84d97800588785efebc2e | b80650c55f544d84be4870a1088cbb2c | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | b33cfe5ac6f3c2ac2ad894c23254b7674506e270e87cd760e93f430ffe1361fe | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4929 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `4aa8768f3fd4b3167071e5598eace1ae7570513009dd1d477bb87d85943742b9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
