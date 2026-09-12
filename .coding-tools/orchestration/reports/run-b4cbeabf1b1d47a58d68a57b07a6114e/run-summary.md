# Orchestration Run Summary

- Run: `b4cbeabf1b1d47a58d68a57b07a6114e`
- Task: `1eebc8855381489faa97be7595ba96b3`
- Objective: Fresh Python full-suite proof shard 1 of 6 for component-state convergence; run exactly these 18 test modules with no source writes.
- Status: **aborted**
- Started: `2026-09-08T17:56:36.417Z`
- Finished: `2026-09-09T07:43:54.571Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ebf5458ef0f3475ca98bb457c4177be5` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44248 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45216 | `SOL_REJECTED` | `ACCEPTING` | Historical non-Problem diagnostic proof shard is still ACCEPTING from 2026-09-08 with no source writes. Its proof passed 184 tests plus 85 subtests on worktree fingerprint c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d, which does not match the current worktree fingerprint c6f9071869d4882401a598b4463ab6c5b574382ead7d293a98a6e8830283b931. Reject stale proof rather than treating it as current component-state acceptance. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `9a364e73b0279668c24c24238e71e1ef10ab4e1076b8ee228db47e99982fc71b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
