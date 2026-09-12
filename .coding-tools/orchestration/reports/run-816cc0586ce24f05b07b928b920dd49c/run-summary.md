# Orchestration Run Summary

- Run: `816cc0586ce24f05b07b928b920dd49c`
- Task: `9466d6591dd54aac9b389e5594a988db`
- Objective: Strict-timing mini-canary for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2. Create one normal read-only RUN, obtain a valid proof and final acceptance, operator-ACK the accepted report, then clear this request-scoped projection. A separately pre-armed observer will immediately run the full immutable lifecycle census. Acceptance/probe timestamps must demonstrate the post-clear semantic census occurred less than 60 seconds after this RUN became accepted, specifically testing the historical controller-lease TTL window. No source mutation, restart, ledger-history rewrite, commit, push, clean, reset, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-12T10:39:42.741Z`
- Finished: `2026-09-12T10:40:53.016Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **1**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a9304937d5f94b0c918b019dce307cc5` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f1b85cff74a046d1a512b079944c7c6d | a9304937d5f94b0c918b019dce307cc5 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 8962a8c9cab3f2d5026b41acf61c9f725076630d6e0d6cb35fb5b2a7b327c794 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51588 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `da498c355d426fc6ccc80960c77cab26aa2285c932ef0627aeb616171933265c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
