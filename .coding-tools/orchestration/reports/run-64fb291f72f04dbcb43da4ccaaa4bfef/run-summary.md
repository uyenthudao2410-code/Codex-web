# Orchestration Run Summary

- Run: `64fb291f72f04dbcb43da4ccaaa4bfef`
- Task: `8fb46560e7c14a1cabeffb9c262fb444`
- Objective: Fix EOCL task/run projection isolation only. A task that already has its own task_id must never adopt a workspace-global active orchestration run that belongs to a different task_id. In _reconcile_task_orchestration_projection, first resolve an active run by the current task_id; permit legacy workspace-global fallback only when the current task truly has no task_id. Add a focused regression proving task_id B with no projection does not attach to active run task_id A. Preserve the accepted completion-report ACK repair and all unrelated dirty changes. Explicitly exclude resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py and resources/coding-tools-mcp/tests/test_truth_snapshot.py. No restart, commit, push, package, release, deploy, T3 or C1.
- Status: **accepted**
- Started: `2026-08-21T20:35:46.566Z`
- Finished: `2026-08-21T20:40:34.734Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `3ed2ca8e2596421c8c827fce65b73c78` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `7af1bbcc4371451f8e0ed97c9636e352` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 3 | `02af215e67bb49659823458c901e32b3` | 3 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ae7ae174b14943dbb5d49f39e589d599 | 02af215e67bb49659823458c901e32b3 | accepted | 9eb05072e54ffca9576e23c2d4a4f4e14034bddc | 6dd2f6bc775d417e2c0f373740bafa0bc8a941159abd8e53bc4f159188b5a08e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26354 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 26373 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 26392 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26367 | `CHECK_FAILED` | `PROVING` |  |
| 26386 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `ac7f647355424060b530b16aa6183158621a38c9729fc9936df8eecebe0592c9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
