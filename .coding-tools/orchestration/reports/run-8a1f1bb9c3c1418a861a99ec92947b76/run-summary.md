# Orchestration Run Summary

- Run: `8a1f1bb9c3c1418a861a99ec92947b76`
- Task: `6054f7f6e57e4492b5d429a0f65bceff`
- Objective: Final EOCL acceptance gate for the current bounded two-file Rust test-only repair on base HEAD 9e150020a0c0829a988ffea527d5c8d82132ed65. Reuse the already accepted full cargo test --lib proof for the same current source and the earlier exact-source Node/Python/secret proofs because relevant source has not changed. Run only lightweight integrity/secret/format gates now; do not mutate source. Independent semantic review is PASS with no production/security/public-contract regression.
- Status: **aborted**
- Started: `2026-08-23T04:51:44.524Z`
- Finished: `2026-08-23T04:52:07.420Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a9b1405aa20a47968e44ea384177fb57` | 1 | `run_initial_objective` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28603 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28611 | `EXECUTION_OWNER_MISMATCH` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `17`
- Chain head: `4fe12d8a1d06da531b3e9db0e5416cb0b24c7b66673014bade04e2c2cd821968`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
