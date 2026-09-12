# Orchestration Run Summary

- Run: `babe1bae0d534f0f8421374227adcd5a`
- Task: `fdc8e919d23e4558a8fceb7b0a296248`
- Objective: Fix PRL prl-a5bf3e0510b110459e4cf57f5bcde24b: in RecoveryHost.superviseOnce, when the direct serviceSupervisorRestartRequest attempt returns status=deferred with a retained durable restart journal (notably transient RUNTIME_BUSY while the initiating task_control call is still leaving admission), do not fall through into orchestrator.supervise in the same watchdog tick because orchestrator.supervise calls serviceSupervisorRestartRequest again. Return a fail-closed transitional supervision projection for that tick; allow the next watchdog tick to retry. Add a focused regression test that reproduces deferred-first then accepted-on-next-tick ordering and proves no same-tick second consumption, no ordinary supervise/recovery/UI work on the deferred tick, and the accepted tick yields immediately for handoff. Preserve all activation fences, durable journal semantics, exact identity checks, and unrelated dirty worktree changes.
- Status: **accepted**
- Started: `2026-09-11T09:22:00.731Z`
- Finished: `2026-09-12T02:24:47.176Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **6**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `49b4e416a83246388ec37965b0c0a0d0` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `4646382c8ddc418a80c229d6b7268a96` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `93b2dfd07b7f48d299e3c76658930ae3` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `6f97b7af8d3d4d128606a056be94bbdb` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 5 | `e34a310a93c64eda99970eab38ecf51b` | 4 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 6 | `be50a141133449bc926a29fae76a04e4` | 5 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a911774f951e405aa00a13df119f9940 | be50a141133449bc926a29fae76a04e4 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | df4808e2272363a7a39c5b0c029125b71019429d9ab7c16d0812d2afa27cd7e7 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 49677 | `auto` | `deterministic` | caller_supplied_change_set |
| 49688 | `auto` | `deterministic` | caller_supplied_change_set |
| 49836 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 49908 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 49935 | `deterministic` | `deterministic` | explicit_request |
| 49962 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 49680 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 49710 | `SOL_REJECTED` | `ACCEPTING` | Reject this wave as a full-Problem closure claim because its recorded proof establishes the regression oracle but does not yet establish the live handoff_drains and exact_stale_postflight criteria. Preserve the applied bytes; replan the same RUN around live controlled-restart evidence rather than fabricating a complete coverage manifest. |
| 49845 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 49923 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 49950 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `326`
- Chain head: `0ec6738f6d548fe6b72ddcbf21169e5517df57d43a6a365e26b7e46224cd43c8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
