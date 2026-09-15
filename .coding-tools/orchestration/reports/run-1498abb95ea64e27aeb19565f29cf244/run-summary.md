# Orchestration Run Summary

- Run: `1498abb95ea64e27aeb19565f29cf244`
- Task: `39f462992eaa4d3fb7178f531f779e5b`
- Objective: Resolve the reproduced controller-lease lifecycle failure that blocks C01 packaging. Determine whether tests/test_execution_hub_faults.py has a stale assertion or acceptance/finalization code violates the canonical terminal-run lease contract. Treat the current lifecycle invariant as authoritative only after comparing implementation plus tests: terminal accepted/CHECKPOINTED runs must not retain a stale controller lease; if historical-run acceptance needs a temporary reclaim, it must be released/terminalized consistently after acceptance. Make the smallest causal correction. Required proof: reproduce the exact failing historical-run acceptance test, apply only the causal change, rerun that test, then run the directly affected controller lease/lifecycle tests including the terminal-run lease test. Do not touch packaging/install/reboot/runtime restart/commit/push/release/deploy in this RUN.
- Status: **accepted**
- Started: `2026-09-14T13:47:52.758Z`
- Finished: `2026-09-14T13:51:33.112Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `9d0d6e1b83b541fa8f5c9b83e5b23355` | 1 | `run_initial_objective` | `mcp_only` | `ae04947d5969e9ee92bf1fe7532bf30e186f8280` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 73497e0ebe3c43f8ae4dbc5245525a47 | 9d0d6e1b83b541fa8f5c9b83e5b23355 | accepted | ae04947d5969e9ee92bf1fe7532bf30e186f8280 | 6fe48ebc4a1da21b72e1ee4c7a7581abc9ea88417bc502392b7aeb47a498d1ec | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 55181 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `6f332f8ddf33358f2a42c08b1f3017c66944c229f5bb58757b2e1567f9c269e0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
