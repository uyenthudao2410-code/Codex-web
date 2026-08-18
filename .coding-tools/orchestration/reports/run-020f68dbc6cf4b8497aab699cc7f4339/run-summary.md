# Orchestration Run Summary

- Run: `020f68dbc6cf4b8497aab699cc7f4339`
- Task: `4b64f89096384f39830d1f0b7c5bbf4d`
- Objective: Prepare the bounded P3 placement-control implementation. Inspect exact current code only for CargoCheck/CargoTest request and dispatch, ValidationRunRequest/ValidationHandoff, run_readonly_validation and run_readonly_validation_agent placement/start_job/handoff/terminal projection, ShellJobValidationMetadata validity, validation job projection, strict Cargo/Job schemas, and compile-impact literals. No source changes in prepare.
- Status: **accepted**
- Started: `2026-08-17T23:51:39.758Z`
- Finished: `2026-08-18T00:10:28.641Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f198fe6b0aca44699bb6900986a5e941` | `mcp_only` | `bc17700e475ce74c96a9547117aade58823f0811` | replanned |
| 2 | `9662ba10c3cb4a15b823c5b4c033fdf5` | `deep_single_lane` | `bc17700e475ce74c96a9547117aade58823f0811` | replanned |
| 3 | `6f2ce5e9c4e34981bf1058217fb4d627` | `mcp_only` | `bc17700e475ce74c96a9547117aade58823f0811` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 1270e9d9ea5d441ca133ea7d37829fda | 6f2ce5e9c4e34981bf1058217fb4d627 | accepted | bc17700e475ce74c96a9547117aade58823f0811 | c2538e6fb61774294f6f8dcfcdf54e7b6f0743b2a4ad50f9d71ae9371585c4e9 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16063 | `deterministic` | `deterministic` | explicit_request |
| 16118 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 16137 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16088 | `SOL_REJECTED` | `ACCEPTING` | Rejecting Layer 1 proof because the authoritative worktree has zero product-source diff and the run itself records modified_files/files_modified = 0. Passing cargo checks only prove the unchanged baseline. Replan must materialize the placement-control source changes on this exact checkout and prove a non-empty targeted Git diff before acceptance. |
| 16124 | `PROMPT_TOO_LARGE` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `120`
- Chain head: `81df98e8dc027574816fcba6767f787476281db2b058fcc0e3df2f776d7abde0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
