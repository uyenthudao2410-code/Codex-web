# Orchestration Run Summary

- Run: `6f62b7ad85034167a3889a4dd996f6bc`
- Task: `279305e566af490b921afa3b05e1c8c0`
- Objective: N21 causal fix. Replace per-RUN exact stale maintenance with one bounded, atomic exact-ID batch so a single explicitly requested maintenance restart can reconcile all currently eligible zero-ownership stale RUN IDs without partial-prefix mutation. Preserve fail-closed guards: one immutable preflight batch snapshot must validate every exact target, reject any below-threshold/live-owned/P5/accepting/unrecognized target before mutation, bind all per-run activity/event guards, then one immediate transaction must revalidate the same logical snapshot and all targets before writing any target; one postflight must prove every target has the exact reconciliation receipt and intact hash chain. Raise the exact maintenance batch envelope only as needed for 64 IDs while retaining the ordinary supervisor restart reason bound. Update the CLI and FullCleanActivation to invoke batch preflight/reconcile once per batch rather than spawning per RUN. Preserve current unrelated dirty bytes in fullCleanActivation/runtimeOrchestrator/recoveryHost and all other files. The already-present RecoveryHost HANDOFF-yield fix is in scope only for verification, not rewriting. No restart in this wave; no reset/clean/commit/push/package/release/deploy. Add focused regression tests covering >16 IDs, atomic rejection/no partial writes, below-threshold/live-owned protection, batch CLI/FullClean invocation count, and existing handoff reconnect behavior.
- Status: **accepted**
- Started: `2026-09-11T03:15:30.430Z`
- Finished: `2026-09-11T03:46:55.162Z`

## Outcome metrics

- Waves: **7**
- Route decisions: **7**
- Failures observed: **6**
- REPLAN transitions: **6**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `875af05472e74997b393b13d4df0e410` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `50a17349a9054fcb8e2da897a7865cbe` | 2 | `replan_request` | `deep_single_lane` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `a52b53a39cbb48fcb98e6908c8fd3244` | 3 | `replan_request` | `deep_single_lane` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `036dadac44d244d1b5048b50eca2e1ea` | 4 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 5 | `1ea6d625f0bd4164a1bcda0e5f9dc9b5` | 5 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 6 | `a749e1c3a70f42029d9cd5611ed3c8cc` | 6 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 7 | `b99a5be7a62343378994b7a30d0956a0` | 7 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4b72327b875345ba819cdbb8fe47bfe9 | b99a5be7a62343378994b7a30d0956a0 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 98a653a75c2613a0bd57dcc02c442c50ce1b48ac8225a03aeec848326e0dec7d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 48612 | `deterministic` | `deterministic` | explicit_request |
| 48643 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 48668 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 48716 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 48764 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 48774 | `deterministic` | `deterministic` | explicit_request |
| 48788 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 48627 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 48648 | `CANDIDATE_SCOPE_MISSING` | `ROUTED` |  |
| 48676 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |
| 48731 | `SOL_REJECTED` | `ACCEPTING` | Reject partial N21 wave: only the atomic ledger batch authority was added; CLI, immutable batch preflight/postflight wrapper, FullClean single-batch invocation, 64-ID exact maintenance envelope, and regression proof are still missing. Preserve the current source bytes for exact adoption in the next wave; no rollback/reset/clean. |
| 48767 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 48780 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `230`
- Chain head: `8472b3a1abb2df938d5130adc92d4598067a4a18c83329f943f5b0d9660cc601`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
