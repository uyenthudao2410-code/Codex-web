# Orchestration Run Summary

- Run: `6dacd9e0edc9482ab18bf711f6f5376b`
- Task: `e335554e0324435190c552631ab8256c`
- Objective: Final read-only closeout proof for the exact stale-run maintenance completed in this session. Collect a fresh immutable lifecycle census after restart #3, then exact read-only probes for c9a67701e8554ce2b21e3117212797f6, 9c633d2185d84ed4b86fa60f6bfb38ef, 6559ba677eb742139c6f111e760edc78, and separately 85aebc6dcb0d4cdbab3c1f91c813eae4. Confirm SQLite integrity, foreign-key status, projection drift, live ownership/unbound-resource residue, stale/unresolved status, and whether 85a remains below threshold or has changed eligibility. Do not reconcile, mutate source, restart runtime, edit ledger history, commit, push, clean, reset, package, or release.
- Status: **active**
- Started: `2026-09-12T09:42:31.332Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8e770686b6a74f6e90fc6030e357c5ed` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51115 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 51149 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `5b4c8051c4f16937eb48b9547823ffd3e28744f4cb99619a53e39b7148d102ab`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
