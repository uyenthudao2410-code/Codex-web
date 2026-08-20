# Orchestration Run Summary

- Run: `acf034cda1474e88a6d24a3091830954`
- Task: `3a0c767915f445a9b062222093289113`
- Objective: Run a pre-checkpoint source acceptance battery over the accumulated P4 validator, control-plane ACK compatibility, benchmark harness, dormant P5 treatment planner, and P5 measurement implementation. This is verification only: do not change source, readiness thresholds, treatment state, or promotion policy. Require raw research stress clean, multilayer normal+strict clean, focused Python regressions clean, diff hygiene clean, and packaging/build smoke clean. Do not commit, push, restart, deploy, or activate treatment in this wave.
- Status: **accepted**
- Started: `2026-08-20T04:33:26.499Z`
- Finished: `2026-08-20T04:39:30.290Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `64bf2fa8cc9545a5ae0aa4fa26d17265` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | replanned |
| 2 | `8691142367454e2b9c7f460e8edd51c2` | `mcp_only` | `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6bb563abd929401e99339ba63021a4e2 | 8691142367454e2b9c7f460e8edd51c2 | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | fabf46670acf0d1d19c4ed8efdf63b4d1a9a6c8dc0157cec23f2106ebae8b5db | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 22592 | `deterministic` | `deterministic` | explicit_request |
| 22639 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 22633 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `eec6b2925d7779732fd55ac1886fa4116e120be9cac89604c6123c7e62e64a99`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
