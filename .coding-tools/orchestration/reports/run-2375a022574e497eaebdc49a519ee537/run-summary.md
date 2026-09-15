# Orchestration Run Summary

- Run: `2375a022574e497eaebdc49a519ee537`
- Task: `bca5f413da5b4da3a8b8b48a8d0d1625`
- Objective: Read-only diagnosis of RUN_CONTINUATION_CHECK_HASH_MISMATCH when issuing a fresh bounded continuation grant for the current Problem. Locate the exact runtime/source function that normalizes approved_checks and computes or validates definition_hash, including the exact argv/cwd/environment inputs. Determine the correct descriptor shape/hash for the focused continuity pytest check without creating a grant, RUN, source mutation, task lifecycle change, or restart.
- Status: **active**
- Started: `2026-09-15T08:02:04.016Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f7cab4a343f341a3afe3c45918e067bc` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `ecae76662a1441008c04b85f7056c844` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `2b5280c84fe647aaaa0c57a9d7062785` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58231 | `deterministic` | `deterministic` | explicit_request |
| 58251 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 58219 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 58241 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 58265 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `a55b99b40c1cac41f57d952513da210ed51f36ba717c67a933a623d852ae3a48`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
