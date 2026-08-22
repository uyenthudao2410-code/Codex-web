# Orchestration Run Summary

- Run: `088f7fb2b94647088eaac26b32595372`
- Task: `06df49de4e1e44df8b13787ab9717659`
- Objective: Fix the observed cross-session agent_workflow task/run objective-binding regression. When agent_workflow is called with an explicit objective for a new material workflow/run, that caller objective must be the canonical run initial objective and wave effective objective. The current/global task projection may be updated to reflect it but must never override it with unrelated prior/concurrent task semantics. Reproduction: explicit Wave A feature objective produced run fd8fad90f9794b0fad39893b58c1a73e whose persisted objective was an unrelated Antigravity port-5260 diagnose task. Preserve task history, existing T1 objective revision/hash/source semantics, smart-v3=8, EOCL authority, and unrelated work. Add deterministic regression proving explicit workflow objective wins despite stale/foreign task projection. Do not implement Wave A in this run.
- Status: **active**
- Started: `2026-08-22T10:06:57.977Z`
- Finished: `None`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `e36e8c8856754657b446f84291f39e3f` | 1 | `run_initial_objective` | `mcp_only` | `3538c761f174f8f609090b31ef368c064df0a5fc` | replanned |
| 2 | `ec295c12b24f4d2691762345659b36b4` | 1 | `replan_request` | `mcp_only` | `3538c761f174f8f609090b31ef368c064df0a5fc` | replanned |
| 3 | `197361a2d641496d902736160230a0aa` | 1 | `replan_request` | `mcp_only` | `3538c761f174f8f609090b31ef368c064df0a5fc` | replanned |
| 4 | `9693127549264e698aa8366933d0be23` | 1 | `replan_request` | `mcp_only` | `3538c761f174f8f609090b31ef368c064df0a5fc` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27052 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 27070 | `deterministic` | `deterministic` | explicit_request |
| 27087 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 27105 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27064 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 27081 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 27099 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `77`
- Chain head: `bf6f86e90148d3c4189c5911a443285009b40bc8474dbd4ae8cff3d7cf0567ef`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
