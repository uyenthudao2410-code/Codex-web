# Orchestration Run Summary

- Run: `52f38c82d9cb4ac4b8b1f581e2ea3698`
- Task: `879622b7d74646cc85189620e077fa02`
- Objective: Run the final read-only decision-science reports on the current repaired worktree without mutating source or opening treatment. Produce accepted-result economics, P2 stratified rework diagnosis, organic rework baseline, P4 readiness/P5 gate, and P5 baseline. Treat readiness nonzero exit as a gate result, not permission to alter policy. Preserve treatment, automatic activation/promotion, auto routing, auto handoff, and global server-first as OFF.
- Status: **accepted**
- Started: `2026-08-23T04:47:50.864Z`
- Finished: `2026-08-23T04:49:28.483Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `a58f63876a5648c29f14706b68192773` | 1 | `run_initial_objective` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 2 | `82f36d8aefa64c4d9f9b864b0a761d9d` | 2 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e6cb6dc0db774c048b94d2a35d80c246 | 82f36d8aefa64c4d9f9b864b0a761d9d | accepted | 9e150020a0c0829a988ffea527d5c8d82132ed65 | 59e66faab6492a970bf22b8db7188f44a1c508b6dfae0fc52b5983845d721a83 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28544 | `deterministic` | `deterministic` | explicit_request |
| 28578 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28570 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `a98967b99898e0a9cf67cd8cd700eb32f179ae5b3b1b9d6ce43d448092c6eb48`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
