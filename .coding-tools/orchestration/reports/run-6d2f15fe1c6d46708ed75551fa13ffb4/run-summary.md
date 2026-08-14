# Orchestration Run Summary

- Run: `6d2f15fe1c6d46708ed75551fa13ffb4`
- Task: `6975ba36abd54702b358bc7926b60c3e`
- Objective: Complete the lifecycle/economics correctness fix from the single paid Flash canary evidence without any further provider inference. Correlated finish=tool-calls must remain an active dispatch step; aggregate per-message measured economics idempotently; emit canonical UsageEvent only at true delegation terminal or Adapter terminal failure; freeze conflicting post-terminal metadata; add bounded Adapter lifecycle evidence and a specific idle-timeout-after-tool-calls error. Preserve canary utility/package and all public contracts.
- Status: **accepted**
- Started: `2026-08-14T13:00:25.021Z`
- Finished: `2026-08-14T13:05:46.116Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `692542f65f834d0a85f9c255a1711a72` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | replanned |
| 2 | `573d50c53df8453381332614a4f13912` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | replanned |
| 3 | `cc8e77a60c12468794bc7937e4266f23` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a3a2b2f2a82f4b08ba5140c0137aa23a | cc8e77a60c12468794bc7937e4266f23 | accepted | bf072d9bd08a14768b729c1d209367bc771633a5 | 0e56609bf58c5e578ff8bc587ffb84e862ba2118f7cdfe8ba51d46de9964e8b4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2092 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 2102 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 2113 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2096 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 2108 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `3f651b4fbfde58330df4adf5344b6574fea63b30b11341658ebd210d27d11c01`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
