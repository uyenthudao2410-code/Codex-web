# Orchestration Run Summary

- Run: `ef61530282f94f1888ac8ef6aa85af27`
- Task: `ab672603a46c4edcb035be20a00c2829`
- Objective: Final integrated acceptance for stale-orchestration health semantics on the exact current worktree. Verify the read-only stale candidate refactor, current-vs-reconciled recovery projections, all existing P1 continuation/idempotency/provenance behavior, and root Electron/Node source contracts. Do not mutate source, restart runtime, commit, push, release, change CI billing, activate semantic credentials, or promote routing.
- Status: **accepted**
- Started: `2026-08-15T02:56:01.701Z`
- Finished: `2026-08-15T02:57:57.103Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9811772d705240bbb877451b3a296fd8` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7f9e9a9a8028460f8bce37b15b73ee0f | 9811772d705240bbb877451b3a296fd8 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 3dceaaf4bf40e1502f6b4b37f899db6b1b1cfc23c0224a83ff5a062cd3ee449f | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3960 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `17`
- Chain head: `284a6941b804a071cfaed5162628ac88d4f617d85cd5d70ca62d578d86e9f948`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
