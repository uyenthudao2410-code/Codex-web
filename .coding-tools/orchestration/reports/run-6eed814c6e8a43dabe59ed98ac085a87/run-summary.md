# Orchestration Run Summary

- Run: `6eed814c6e8a43dabe59ed98ac085a87`
- Task: `f4ffd6a707ad45f2b3bd082406c74196`
- Objective: Run a fresh read-only exact stale-run maintenance preflight for the three previously scoped stale RUNs c9a67701e8554ce2b21e3117212797f6, 9c633d2185d84ed4b86fa60f6bfb38ef, 6559ba677eb742139c6f111e760edc78, and separately inspect 85aebc6dcb0d4cdbab3c1f91c813eae4. This diagnostic RUN exists only to give the read-only census commands canonical EOCL ownership so they do not appear as unbound live resources. Do not reconcile, mutate source, restart runtime, commit, push, clean, or reset. Preserve all dirty WIP. Report exact eligibility, live ownership, unbound resource residue, projection drift, integrity/FK status, and stale-threshold status for each target.
- Status: **accepted**
- Started: `2026-09-12T09:16:40.446Z`
- Finished: `2026-09-12T09:18:55.708Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `cf3a4dd9601c48d7913e81d157c34ef3` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `867132fe0db84e20a04ef5fa1eeae41e` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 28fb63d4cfe745e7ba240788002aec5e | 867132fe0db84e20a04ef5fa1eeae41e | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 3d095f68c81423aacdbd9942fb8ddfba35f702972d6521d8773a217eec33ca4c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50961 | `deterministic` | `deterministic` | explicit_request |
| 51001 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 50990 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `24610e000f9b361ec7f1a6294f97b13bd99c458acfd53904fbeddb0ea3502b8a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
