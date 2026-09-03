# Orchestration Run Summary

- Run: `2f423a1f84f144d59e73dc4af29bba07`
- Task: `52f4175ae2d34d0f919a1138f6ffc0a1`
- Objective: Complete an end-to-end workspace workflow
- Status: **accepted**
- Started: `2026-09-03T04:15:49.043Z`
- Finished: `2026-09-03T04:26:24.082Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a1881186116b4431bef1b273401c93e6` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `9afe5ec5e6cd4958a1f4ec3063113687` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 70cd7bc0bfe94e008a22958c2dba2855 | 9afe5ec5e6cd4958a1f4ec3063113687 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 3d4b6ebc9b13ec81b90734527f8ab1387ac79b8f55ae5120da4cc69326fca9a6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35981 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36006 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 35996 | `SOL_REJECTED` | `ACCEPTING` | ACCEPTANCE_PROOF_REQUIRED after verification=none; replan to exact artifact proof-only wave without source mutation |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `16b476035b8b6af28d3d95c77bed2b5cca67f94f016d290fe730a948cc1eb20f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
