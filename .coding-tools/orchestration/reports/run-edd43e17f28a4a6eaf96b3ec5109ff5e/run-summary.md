# Orchestration Run Summary

- Run: `edd43e17f28a4a6eaf96b3ec5109ff5e`
- Task: `3d28db5e626b4bb0a01514dd37917d40`
- Objective: Close the controlled-replay causal-acceptance gap without adding a public tool or inferring success from process exit code. After each isolated trial command, read that trial workspace's authoritative EOCL orchestration ledger and attest exactly one accepted run whose evaluation/source identity matches the trial manifest. Require an accepted checkpoint plus proof/oracle evidence, and fail closed on missing, ambiguous, identity-mismatched, or route-policy-mismatched evidence. Preserve existing plan-only and no-ledger behavior.
- Status: **accepted**
- Started: `2026-08-15T10:59:03.535Z`
- Finished: `2026-08-15T11:03:14.806Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `d3fcfa1371544db3adf687c926da2063` | `mcp_only` | `f64abe25a85e6abaa9fe9eeacd3665eb29a82515` | replanned |
| 2 | `9453bd0b9f2f4bedac3aeb8b25632c4d` | `mcp_only` | `f64abe25a85e6abaa9fe9eeacd3665eb29a82515` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 068be57f95824fa79743bf29f89e8d04 | 9453bd0b9f2f4bedac3aeb8b25632c4d | accepted | f64abe25a85e6abaa9fe9eeacd3665eb29a82515 | 84c78116455abe2291bb193b9efbd39bd8ee412a219961eaecb406752f7732f2 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5306 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 5320 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5315 | `SOL_REJECTED` | `ACCEPTING` | Focused tests pass, but acceptance review found one fail-closed gap: each accepted trial is individually attested, yet the executor does not verify that both policies in a pair have the same EOCL pair_fingerprint/worktree identity. A caller command could mutate source before EOCL run creation and still yield individually accepted evidence. Add pair-level fingerprint equality before declaring accepted_result_evidence_complete. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `09bd841cd548ef4572bdf28648655b8d06706288e630c26cd721057845fc55c0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
