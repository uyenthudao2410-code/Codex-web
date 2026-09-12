# Orchestration Run Summary

- Run: `5ed4115abd52443fbc4a5b1034cbe0dd`
- Task: `750411b0c11f424ebba1ab114da52e9b`
- Objective: Make Recovery Supervisor reinstall replace an orphaned prior supervisor cooperatively and fail closed unless the exact newly installed capability-bearing process publishes a fresh heartbeat.
- Status: **accepted**
- Started: `2026-09-08T14:27:35.393Z`
- Finished: `2026-09-08T14:28:44.909Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a93d2c5e325a4d22a8fb5b9341eae4f5` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fc1fc9b52c1d4d1a9b699bcb9aa26dae | a93d2c5e325a4d22a8fb5b9341eae4f5 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | c7903cfe89973fa3f2e01437eb926ac0dbe0fdbbb813735e3719620ac354df50 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43941 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `0e578347e0823b6f5388a5aa3490a7565e9eb99c52caa4ed28906655f08c871a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
