# Orchestration Run Summary

- Run: `237fb771ddc54807a31d42680353cd97`
- Task: `a1d630a60be04d0a94672952c17709c8`
- Objective: Production canary for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2 after automatic source activation. Run one immutable lifecycle census summary under canonical EOCL ownership on the newly activated runtime. This canary is intentionally read-only; it exists to create a normal accepted terminal RUN under the new orchestration_ledger behavior so we can immediately clear the request-scoped task and inspect whether the just-terminalized RUN leaves a live controller lease / false TERMINAL_PARENT_CONTRADICTION inside the former 60-second window. Do not mutate source, restart, edit ledger history, commit, push, clean, reset, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-12T10:22:32.685Z`
- Finished: `2026-09-12T10:33:54.191Z`

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
| 1 | `7538b26878014fc191fff02e09e80edf` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `7d87fd7450cd454fa3ba40123caa307c` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3a5ea641db3240cdbf824b0ca9c16137 | 7d87fd7450cd454fa3ba40123caa307c | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 77de8612673afe505b43d0ed3ccb6b426cda990d1752d1e66560c2beafa84487 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51491 | `deterministic` | `deterministic` | explicit_request |
| 51521 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 51508 | `SOL_REJECTED` | `ACCEPTING` | Do not accept this live canary from exit code alone. Its command output has expired from the process-retention plane before controller inspection, so the semantic lifecycle fields (projection_drift, missing_run_count, terminal-parent contradictions, unbound resources, integrity/FK) cannot be independently verified. Replan the same RUN for a fresh census and inspect the payload immediately; preserve this retention miss as self-repair telemetry. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `677b3da6f1d4f0613b591cdb78105e66bb5d2ed0981fa39207e71b67718c7c4e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
