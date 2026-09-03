# Orchestration Run Summary

- Run: `85c36411deeb411c8ac8a0f3cc6e69c1`
- Task: `284a6e67fb564031bd3b42eca280458c`
- Objective: Continue RUN 4ccf77eee93d4cfba07e46609157d04e with a new corrective wave after the pre-write SOLUTION_SHADOW_REQUIRED gate. Fix the Full clean activation race that causes ACTIVATION_EPOCH_STATE_REGRESSION: RecoveryHost.superviseOnce must run replacement watchdog final-census only in post-handoff assembly states STARTING or VERIFYING, never in PREPARING, ADMISSION_CLOSED, FROZEN, STOPPING, or HANDOFF. FullCleanActivation.recordPendingCensus must fail closed without mutating the durable epoch unless current state is STARTING or VERIFYING; preserve STARTING -> VERIFYING and VERIFYING evidence refresh. Add deterministic regressions proving STOPPING is not advanced by watchdog, pre-start/pre-handoff recordPendingCensus rejects without mutation, STARTING and VERIFYING remain valid, and existing duplicate/finalization semantics do not regress. Preserve all unrelated dirty worktree and .coding-tools evidence. No adoption or force-release. No commit/push/tag/release/deploy/restart/activation. Use only the supplied four paths.
- Status: **accepted**
- Started: `2026-09-01T16:01:30.972Z`
- Finished: `2026-09-01T16:10:33.355Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `6114ac96e2314a1bbf8af620977cd41e` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `7ade2b7ad26843978ea4d63c89246cf0` | 2 | `replan_request` | `bounded_candidate` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `4e214cfdbe294ce9b437a8f472478488` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 4 | `9c3d8207d2c040f2875aa7f17b808975` | 4 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 5 | `615de499e59a48ba921cab273f71b46d` | 5 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d6cebab8e9e44c149a14af4a3dff1e6f | 615de499e59a48ba921cab273f71b46d | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 9581a93bd084ed0c7453c2d692ebbff07b7c0d7258c09bfed01dfc83290ba6f4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 34606 | `deterministic` | `deterministic` | explicit_request |
| 34638 | `luna` | `luna` | explicit_request |
| 34652 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 34679 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 34708 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 34627 | `SOL_REJECTED` | `ACCEPTING` | Reject to REPLAN: deterministic execution ran only the pre-existing focused suite and produced modified_files=[] with no write lease. The old oracle does not discriminate the reported STOPPING watchdog/state-regression race, so the requested implementation and regressions are absent. |
| 34645 | `CANDIDATE_REPORTED_BLOCKED` | `ROUTED` |  |
| 34672 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 34701 | `SOL_REJECTED` | `ACCEPTING` | Reject to REPLAN because final acceptance correctly requires current-wave file attestation: three exact files were mutated under prior wave 3, whose proof failed, while wave 4 leased only the fixture file. Do not adopt or force-release. Consolidate the same causal fix under one new four-path lease, then rerun exact proof. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `132`
- Chain head: `1a2cafc28aa67b8ed4ddb35ed93dec2b08d9613e2c333c12109e21dacdfd1b55`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
