# Orchestration Run Summary

- Run: `46ebec3dce7c4b4cb83ed3c503a1bdc8`
- Task: `5b1270878a7a474fb54e03349d7c7f2e`
- Objective: G2 corrective regression closure on current HEAD 8697ace8204e7e3da55d250d4a52d9b2b930116c: change only resources/coding-tools-mcp/tests/test_exception_group_boundary.py by adding self.task_state = SimpleNamespace(get=lambda: {}) inside FailingRuntime.__init__ for test_http_pre_dispatch_boundary_never_stringifies_exception_group. Preserve all concurrent WIP, keep production behavior unchanged, do not modify the two already-passing regression tests or any second path. Run focused three-test selection without pytest :: node IDs, then full npm test:all, module-size guard, git diff --check, and exact target-file diff inspection. Stop/replan on any drift or failed proof.
- Status: **accepted**
- Started: `2026-09-04T11:36:33.056Z`
- Finished: `2026-09-04T15:26:53.390Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **17**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `1965ee5817064f999db57bc43083bf3b` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 2 | `35e07b6c64fc4638ab0bb7cb145fd221` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 3 | `07e02bc35fb442c9bc43ac3fd0730819` | 2 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 4 | `20c549c4e3c94e59b25190457a383f11` | 3 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 5 | `623448108a3343f8b610c8e701689d1f` | 4 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| bf188b4106c9465196549d9e91f92818 | 623448108a3343f8b610c8e701689d1f | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | f0ed75e90295fbc734eba2dfe8d96b48abcb117612b804e39266d41a14ac3996 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 39712 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 39968 | `deterministic` | `deterministic` | explicit_request |
| 40073 | `deterministic` | `deterministic` | explicit_request |
| 40106 | `deterministic` | `deterministic` | explicit_request |
| 40128 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 39732 | `CHECK_FAILED` | `PROVING` |  |
| 40066 | `SOL_REJECTED` | `ACCEPTING` | SOURCE_OR_STATE_DRIFT_POST_PROOF_6CEA96E7_TO_010F1467_TARGET_UNCHANGED |
| 40099 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 40121 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `183`
- Chain head: `caab9385981a9d5463256d69b81b22c011156d1dfafcff04b6eee2cce6d10fc2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
