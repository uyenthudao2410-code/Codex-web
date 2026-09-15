# Orchestration Run Summary

- Run: `d44f52e1b8504d8682c3771229414d3f`
- Task: `ab0b1f8ecea548ad9f2219847b057ed5`
- Objective: Create the smallest exact-byte source-authority consolidation for Problem prl-e918c7d33e70c2d304d0797e11b05fcb rev2 needed to unblock the already-authorized controlled runtime restart. Current Recovery Host component dirty surface is exactly electron/services/recoveryHost.js, electron/services/runtimeOrchestrator.js, and untracked electron/services/controlPlaneReadOnlyBridge.js. Do not edit these files. Inspect their current delta and existing tests, prove the exact current bytes with strong targeted Recovery Host/runtime lifecycle/accepted-code activation/activation-closure checks plus git diff --check, and if all proofs pass prepare them for exact-byte adoption/final controller acceptance only. Do not accept unrelated dirty files, do not restart in this wave, do not interfere with C01 packaged-supervisor RUN, do not reset/clean, commit, push, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-15T09:19:15.923Z`
- Finished: `2026-09-15T10:23:25.725Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `9c6c50c1a23e4fa18c5ead7f9576137d` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `02cc5869774f4e4bbf0ba3cf88b73e27` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 8561befdf638488292cc41c25bd88232 | 02cc5869774f4e4bbf0ba3cf88b73e27 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 120cd7ff1a9c62247899978099513e2c51101f6a0697293eb5e4d8bf382173a3 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58892 | `deterministic` | `deterministic` | explicit_request |
| 59273 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 59204 | `SOL_REJECTED` | `ACCEPTING` | Fail-closed rejection of stale acceptance after exact source drift. Current live bytes differ from the bytes proven by wave 9c6c50c1a23e4fa18c5ead7f9576137d. No deterministic durable writer receipt was found in the write-time window, so record this as unattributed shared-worktree SOURCE_OR_STATE_DRIFT; preserve this exact RUN for replan and do not restart runtime. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `109`
- Chain head: `89c02082ea31ca1968dabe870dc8a02f51aecd6e6762187f3d4fc3ea8ee7ca71`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
