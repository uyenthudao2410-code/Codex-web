# Orchestration Run Summary

- Run: `507227665bb742e0b95078c0072f21df`
- Task: `79872f4150c14443b86631fba35b5511`
- Objective: Read-only trace of the exact agent_workflow continuation-grant call path that invokes build_goal_continuation_policy/build_run_continuation_policy. Determine which contract_fingerprint value is passed into continuation policy construction and why a canonical 64-hex Problem contract fingerprint can still produce RUN_CONTINUATION_POLICY_INVALID. Do not mutate source, create a continuation grant, restart runtime, or alter acceptance authority.
- Status: **aborted**
- Started: `2026-09-15T08:11:07.897Z`
- Finished: `2026-09-15T08:30:28.898Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `275a64e19e73425895eedcc6d091909c` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `10`
- Chain head: `96460359ed77f6ab7ae1fcacd143a3d9593205524e8302f65dbe462c02fce628`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
