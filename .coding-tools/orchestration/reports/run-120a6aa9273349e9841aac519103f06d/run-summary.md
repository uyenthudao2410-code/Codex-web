# Orchestration Run Summary

- Run: `120a6aa9273349e9841aac519103f06d`
- Task: `b87643e5133947c28c004bc6d76b3bb7`
- Objective: Create one additional no-source-write convergence checkpoint for the exact 40-path remaining accepted-code component boundary at current HEAD, relying on acceptedReceiptUnion across accepted checkpoints so Recovery Host can recompute component eligibility without reopening the prior accepted convergence run.
- Status: **accepted**
- Started: `2026-09-08T18:48:15.296Z`
- Finished: `2026-09-08T18:56:36.558Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `81964c1c08b74f7a8ffcf4f32a6bf567` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `5e62f9d8224548d99e0ae1fdc7624aeb` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a1ac5109e0fa4255918973a14107cd43 | 5e62f9d8224548d99e0ae1fdc7624aeb | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 3b857d96004880ca4aca78250277c6e7928d66cd836715c998e54b76bd9098a8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44437 | `deterministic` | `deterministic` | explicit_request |
| 44493 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 44443 | `ACCEPTANCE_FILE_SHA_MISMATCH` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `3a71cabdaab7fdff8a55477a4abd5d88974146b1ee8fa29423fd887b647d7cd6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
