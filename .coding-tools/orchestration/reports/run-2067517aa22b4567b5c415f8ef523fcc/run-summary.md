# Orchestration Run Summary

- Run: `2067517aa22b4567b5c415f8ef523fcc`
- Task: `57c15212759e493d852c3a7a8672ca40`
- Objective: Final verification-only full-problem closure for Problem prl-8a57cc01ad8abd9f56a14c8bd605229d revision 1. Do not modify source. Re-run the current stage-latency attribution reporter against the explicit immutable source HEAD 7bc1caee37107a15e74eb078b52fe314e5fa33ab and run the focused authority/backward-compatibility regression suite. Use the current natural canonical ledger evidence produced after the runtime activation: the accepted natural run must contribute a same-clock acceptance anchor, controller_processing and acceptance_wait; exact host binding must remain at or above 0.90 without timestamp proximity; explicit source HEAD must remain selected on the dirty worktree; historical missing telemetry must remain missing/unknown rather than backfilled. No synthetic fixture may substitute for natural evidence. No commit, push, package, release, deploy, restart, stale-run reconciliation, or source mutation.
- Status: **accepted**
- Started: `2026-09-12T06:54:49.659Z`
- Finished: `2026-09-12T06:58:38.300Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0376d65067e1435da464de8167834ca1` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 24a73c1aa7224d0299bb22acc83725fd | 0376d65067e1435da464de8167834ca1 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | a50f39b74c269ca0cf8906bbc7756245ef584b3e70f99ac4ffedf6a7ed248790 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50460 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `508905adbf51968154849b0f1dccafe0928ae2f1048e9b3146f3ce9ab6f0ca83`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
