# Orchestration Run Summary

- Run: `c73f328df60d499b848f929719adc456`
- Task: `37ff0cab200843ecb813b05ebb8c8a30`
- Objective: Deep deterministic evaluation of Tools-Codex-web performance, efficiency, and cost without paid provider calls. Locate existing benchmark/economics/profiling scripts, accepted-result economics projections, proof/cache/idempotency telemetry, and representative test harnesses. Do not modify files and do not dispatch external review or candidate models.
- Status: **active**
- Started: `2026-08-15T04:52:07.645Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `5238ff8b0f0345659eaee364f63ae65d` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4276 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4358 | `SOL_REJECTED` | `ACCEPTING` | Reject diagnostic wave: despite explicit deterministic route and external_review=disabled, 22 OpenCode provider delegations were attributed to this wave with measured provider cost. This violates the no-provider evaluation invariant and invalidates the wave's economics. Stop authority and preserve ledger for root-cause analysis. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `87`
- Chain head: `64fc2443ea89a350edb6fef0ab2fca4bb10a73921a1cf8a6e06a923d2d83162e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
