# Orchestration Run Summary

- Run: `8bf171b1fe7346e88cd97c34338c1102`
- Task: `b2ea97d06a6649e1baac3c7037459f37`
- Objective: Fix the observed N21 supervisor restart/full-clean HANDOFF self-deadlock that caused exact maintenance ticket restart-49eqbqg6cR5jzcW7 to fail with RECOVERY_SUPERVISION_BUSY. Root cause already proven: RecoveryHost.superviseOnce consumes an exact restart ticket while the current durable epoch was READY; FullCleanActivation transitions to HANDOFF and stops the runtime, but superviseOnce continues ordinary orchestrator.supervise/recovery/UI work using the pre-ticket admissionBlocked=false value while performFullCleanHandoff waits on the same supervisionInFlight promise. The fix must make the current watchdog iteration yield immediately after serviceSupervisorRestartRequest returns status=accepted, publish only fail-closed transitional readiness, preserve completed/failed/deferred/no-ticket behavior, and add a focused regression test. Preserve all unrelated dirty bytes. Do not modify stale-run reconciliation semantics, timeout constants, ledger data, or Git history.
- Status: **accepted**
- Started: `2026-09-10T17:52:13.921Z`
- Finished: `2026-09-10T18:06:20.657Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ffaa77b74f324c0883df5b692546ae52` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 67a0b107450d44d4a8676142776a2797 | ffaa77b74f324c0883df5b692546ae52 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | e2cc498d683235f7b9e94e08ddcbd3de3bbbc81380ae81206d40c6083dc86672 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 48500 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `9119829b1423c37a1d8817340c91ea8c529e3defeb951d11d195aad721621ebf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
