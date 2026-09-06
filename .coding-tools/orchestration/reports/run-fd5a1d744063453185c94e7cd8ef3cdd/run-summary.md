# Orchestration Run Summary

- Run: `fd5a1d744063453185c94e7cd8ef3cdd`
- Task: `dc7d979fed394b6c8bc0c42dd8e5b2ee`
- Objective: Prepare the already-proven new-machine activation/runtime-path fix for Git delivery on main@573b6ff5a5ff2509288c9656e18fd375f1ab32d3. Run the repository-mandated coding-tools staging and delivery guards, then report the exact staged scope. Do not commit or push in this step. Preserve all unrelated working-tree content.
- Status: **aborted**
- Started: `2026-09-06T05:08:12.972Z`
- Finished: `2026-09-06T05:11:10.690Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `04bbdf4f526249d99a9583edb6b0048f` | 1 | `run_initial_objective` | `mcp_only` | `573b6ff5a5ff2509288c9656e18fd375f1ab32d3` | replanned |
| 2 | `6c8a49cf2a154668b92ca4f38cd39ae3` | 2 | `replan_request` | `mcp_only` | `573b6ff5a5ff2509288c9656e18fd375f1ab32d3` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41295 | `deterministic` | `deterministic` | explicit_request |
| 41324 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41314 | `CHECK_FAILED` | `PROVING` |  |
| 41338 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `735815b4d7e6540fa4c9aacdb4e0e0bd1bdd3e6fad953a887130a0f419062cdb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
