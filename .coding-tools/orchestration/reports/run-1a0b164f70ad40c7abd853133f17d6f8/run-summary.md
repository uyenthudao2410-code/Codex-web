# Orchestration Run Summary

- Run: `1a0b164f70ad40c7abd853133f17d6f8`
- Task: `19a040d801ad4149a82023c718a2fe72`
- Objective: Fix only the nondeterministic timing fixture in the test `new bootstrap terminalizes an expired prior epoch and can create a fresh operation`. Preserve production fail-closed expiry behavior. Replace the 30ms wall-clock TTL plus 40ms sleep with a deterministic Date.now mock: capture original Date.now after RecoveryHost construction, freeze a local `now`, create/update the epoch before expiry, advance `now` past expiry, call prepareBootstrapStart, assert the same FAILED/ACTIVATION_REQUEST_EXPIRED results, and restore Date.now in finally. Do not modify production code or any other dirty file.
- Status: **active**
- Started: `2026-08-28T10:44:20.268Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `c4ee03362eda4e5d871499e03da81680` | 1 | `run_initial_objective` | `mcp_only` | `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32214 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `13aed052c80f758c58a740d58a5263f4307d1d7dfc626fe7eaabe5cba9741333`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
