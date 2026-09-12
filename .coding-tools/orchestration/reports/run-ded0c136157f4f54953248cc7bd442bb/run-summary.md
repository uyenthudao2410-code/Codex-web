# Orchestration Run Summary

- Run: `ded0c136157f4f54953248cc7bd442bb`
- Task: `c035b8d7239742f8a95e0461428871b0`
- Objective: Converge Recovery Host and Coding MCP component state without source writes by no-patch provenance adoption of the runtime-observed Git-dirty subset and exact controller attestation of all 26 current component-file bytes, with fresh bounded deterministic proof covering both runtime components.
- Status: **accepted**
- Started: `2026-09-08T17:59:27.975Z`
- Finished: `2026-09-08T18:32:42.234Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `4b3c9a2a103445feb7e03144e6fdf37b` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `6104d1720b614d5d9e59e4e20c92672f` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `cc61907f1ec14b758b8ed90934d4762a` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `0f0209d5bccd4b8d900d5681a5c37a8b` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| eacee8edd41e4a77a2fe226a92ccfdf8 | 0f0209d5bccd4b8d900d5681a5c37a8b | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 509c3673d700561689b5a24a32d58a48fbd48c2554dae883028f95241d22b052 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44265 | `deterministic` | `deterministic` | explicit_request |
| 44296 | `deterministic` | `deterministic` | explicit_request |
| 44318 | `deterministic` | `deterministic` | explicit_request |
| 44388 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 44289 | `PROOF_TIMEOUT` | `PROVING` |  |
| 44311 | `CHECK_FAILED` | `PROVING` |  |
| 44379 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance proved that app_server_persistence.py and continuation_contract.py are pre-existing untracked dirty paths inside the 26-file acceptance boundary but were omitted from the lease allowed_paths and durable no-write adoption surface. Replan with all 12 dirty paths and do not change source bytes. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `168`
- Chain head: `23362491c5805f3969b52278a3f6c35b09a28a327a3b674d97f7b5982b40bc9d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
