# Orchestration Run Summary

- Run: `306c03f544ba4af6bf1de8777045d227`
- Task: `d99aa7eac9c84ac48d68fcae09f18b95`
- Objective: Packet C4: create a new bugfix RUN without reopening or amending accepted C2. Fix the real ABA fencing defect in resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py and resources/coding-tools-mcp/tests/test_run_continuation.py only. Current behavior: revoke/regrant resets driver_generation=0, so after policy revision 2 a claim by the same runtime_instance_id can receive generation=1 again, allowing an old worker with the same runtime ID and generation to pass assert_run_continuation_execution, reserve a new action, and bind stale dispatch identity. Minimal fix: on regrant do not reset driver_generation to 0; preserve monotonic generation across revoke/regrant, and require the next claim to use the observed current generation as expected_generation then increment. Preserve the no-pending-effects/job gate, full immutable policy behavior, fencing, effect history, schema, public tool surface, and all unrelated behavior. Update the existing C2 regrant regression that hardcodes expected_generation=0 to use the observed new-policy generation without weakening its assertions. Add a focused regression using the same runtime_instance_id proving the old generation is rejected after revoke->regrant->reclaim at assert, reserve, and dispatch boundaries, while the fresh generation can proceed. Do not use any continuation/background driver to modify runtime. Do not touch .coding-tools or any other source file directly. Prepare only in this call; no patch, no proof, no accept, no commit, no restart.
- Status: **aborted**
- Started: `2026-09-08T00:16:37.814Z`
- Finished: `2026-09-08T04:52:56.924Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `12cefe9a10314ec1a0f4d479a0a3933e` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `2c7a5f67f77c47778062e7fe72445367` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 43623 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 43661 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 43654 | `SOL_REJECTED` | `ACCEPTING` | Typed REPLAN for acceptance provenance only: final acceptance failed closed with ACCEPTANCE_FILE_ATTESTATION_REQUIRED because both C4 target paths were pre-existing dirty surfaces inherited from accepted C2. Source and 4 C4 proofs are green at exact live source/worktree fingerprint dfb502935ae9b720966b23687cc08d9278845bb9db66c59ac1fbc6cb54409c2c. Create a same-RUN deterministic/mcp_only wave solely to durable-adopt exact current bytes under the scoped write lease; no source patch, no C2 reopen/amend, no Problem/full-resolution claim. |
| 43679 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `68`
- Chain head: `cd498cc1b84d4cb7522d165c81a89fe8fb73b9fe14c2175f252fa7ffb0d6ef90`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
