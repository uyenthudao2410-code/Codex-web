# Orchestration Run Summary

- Run: `63db31c334b84d24a4d6b7df660fa39a`
- Task: `43a4032ea9fb4aa689e3caf34871707e`
- Objective: Complete only the missing stale-health regression tests; production stale-health source changes are already present. Add candidate-before/reconciled-after assertions and a runtime projection test that proves current unresolved stale health is zero while reconciled history remains visible.
- Status: **active**
- Started: `2026-08-15T02:54:00.814Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c945bc87c9d945339c7088e87c0faaee` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3934 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3942 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `786b6fff7597ea59eb69b8bb42b2f9179bf1980f9e865f01490a36fe31e1f8bb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
