# Orchestration Run Summary

- Run: `d07cc568e2b345bb946754e565a026df`
- Task: `7c317886857e4f0aa59ffe3b3de868b0`
- Objective: Implement Natural #4 exactly: add an opt-in CLI flag --stale-details to the empirical readiness reporter. Default output must remain backward-compatible and compact. When requested, stale_run_audit must include a bounded detail row for every THRESHOLD_SENSITIVE_STALE_CANDIDATE, including both over-threshold and below-threshold candidates, with run_id, activity_age_seconds, meets_current_stale_threshold boolean, latest_state_after, evidence-based subtype via the existing _stale_subtype logic, and last_event. Keep existing sample behavior unchanged. Add focused tests proving default omission/backward compatibility, full candidate coverage including a below-threshold candidate, reuse of existing subtype semantics, and unchanged read-only/no-reconciliation/no-P5 contract. Modify only the two authorized files and preserve unrelated WIP.
- Status: **aborted**
- Started: `2026-09-09T09:33:06.359Z`
- Finished: `2026-09-09T10:15:52.171Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `32d4b12f908e45029b412f29eb599cf4` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `d9284c7392b24ef5a7dead543014adc7` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 45398 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45412 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `52`
- Chain head: `9751cfcb51059e1597b201c5980931e31bd34ea2e1fe3f3dfad9bd871fc61c61`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
