# Orchestration Run Summary

- Run: `ff4a12a96ce549d4871195fc9d77428f`
- Task: `a798268a444147f1b97f5a5ff4bc025c`
- Objective: Complete the remaining non-UI technical roadmap for Tools-Codex-web without changing the Smart-v3 public 8-tool contract. Implement a canonical measured UsageEvent contract/projection with provenance, measured-vs-estimated identity, cached/reasoning token counters, queue/provider/total timing and typed provider error classification; integrate existing OpenCode telemetry into that contract. Implement a Hub-side OpenCode read-only Provider Adapter that can dispatch an explicitly selected allowlisted OpenCode Go model (Flash/Pro) with a bounded prompt packet, timeout/cancel lifecycle, exact run/wave/session/model correlation, usage/cost capture, and fail-closed no-native-write semantics. Implement shadow provider routing as recommendation/evidence only (no automatic mutation or controller transfer), with durable accepted-task route/economics fields sufficient for later cohort calibration. Preserve current controller/write fencing, current routing thresholds, OpenCode worker-only role, existing concurrent UI work, and existing exact telemetry semantics. Do not touch renderer/UI files, do not restart Electron/runtime, do not change permission settings, do not run paid/provider inference solely for proof, and do not commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-08-14T09:34:38.495Z`
- Finished: `2026-08-14T09:40:04.782Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `230cf42e1a264631a86c5af3692d3205` | `deep_single_lane` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `463fbfdecb91459bab8e2fd18418461e` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 3 | `6388754e57ce43d7bb17cf0cbcea2912` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 47188a3ceb59414897f4e2bfc87a5243 | 6388754e57ce43d7bb17cf0cbcea2912 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | 945c3e1acd98b1971f065b6488b7421c144bddd08d0d54b395b2359d2a1e622a | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1729 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 1738 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1751 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1733 | `CANDIDATE_SCOPE_MISSING` | `ROUTED` |  |
| 1746 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `98be1f371f0f6a3a76beb00d30c943e7e27fef27d4e71efeb254dab6e4fa67ed`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
