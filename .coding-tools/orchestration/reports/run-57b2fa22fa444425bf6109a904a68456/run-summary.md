# Orchestration Run Summary

- Run: `57b2fa22fa444425bf6109a904a68456`
- Task: `b6269981fbb345e9b89d2dedc7e89a8c`
- Objective: Fix the proven deferred-observer race only in scripts/full-clean-activation.js: when waitForReplacementReady has already matched the exact replacement descriptor epoch, exact status epoch, and exact operation_id, but runtime.lightweight_snapshot transiently reports a prior activation epoch from the Recovery Host supervision cache, classify only that runtime-snapshot epoch mismatch as retryable ACTIVATION_HANDOFF_PENDING so the existing catch/poll loop waits. Preserve fail-closed descriptor/status/operation mismatch checks and require the runtime snapshot epoch to match exactly before READY. Add one focused regression in tests/full-clean-activation-command.test.js where the first lightweight snapshot reports a prior epoch, the next reports the exact epoch, and readiness returns only after the exact snapshot without terminal ACTIVATION_OPERATION_MISMATCH. Preserve all unrelated dirty WIP and do not touch .coding-tools manually or protected foreign lineage.
- Status: **accepted**
- Started: `2026-09-08T20:45:47.314Z`
- Finished: `2026-09-08T20:50:34.889Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `16a897a7fa1c4f709a880b643eb74436` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 8d3bc91d6f4e49aca30a15fdd63a4f0c | 16a897a7fa1c4f709a880b643eb74436 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | ee0cbb46abc9dbbffb4b3d1c061098c4eade7a08ca2f87104d4c7da01b72e628 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44697 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `3293d8f2b052abec6786e9300f35c8841838daffdab2c89b487b6df7ab79dcac`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
