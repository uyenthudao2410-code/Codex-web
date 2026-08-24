# Orchestration Run Summary

- Run: `c6080cf425fa4bd4addbf64f4f6e7786`
- Task: `5ced2b1d809f497db0736dbc02e12b17`
- Objective: Resolve the exact-source Rust cargo test --lib closure failure on HEAD 9e150020a0c0829a988ffea527d5c8d82132ed65 without broad refactoring. The prior full Rust lib proof timed out and retained output showed failures in tool_runtime metadata, handoff_brief, and two jobs tests. First discriminate test-isolation/global-state contamination from real source-contract defects by running the failing groups/tests serially and exactly. Do not mutate source unless a reproducible isolated failure proves a causal source defect. Preserve smart-v3=8, current P5/source authority, EOCL, and all already-passing Node/Python behavior. If a source fix is necessary, make the smallest coherent change and run focused proof only; do not rerun the same full cargo test unchanged in this wave.
- Status: **aborted**
- Started: `2026-08-23T04:34:45.544Z`
- Finished: `2026-08-24T10:52:04.788Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **4**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `213fd7b1b60f49c2914a9396826ce806` | 1 | `run_initial_objective` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 2 | `55e2979897e64b5aab944ebff5730b02` | 2 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 3 | `ce7290cb1bf34c0d9b795bb867b00adf` | 3 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 4 | `a7d954cbbd024df2a14cec134442426c` | 4 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 5 | `ebc9cde02c254cc6933777312d368d6e` | 5 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28287 | `deterministic` | `deterministic` | explicit_request |
| 28305 | `deterministic` | `deterministic` | explicit_request |
| 28329 | `deterministic` | `deterministic` | explicit_request |
| 28348 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28293 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 28297 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |
| 28321 | `CHECK_FAILED` | `PROVING` |  |
| 28340 | `CHECK_FAILED` | `PROVING` |  |
| 28359 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `84`
- Chain head: `1553520b612a067e907d206e09c9e0dee9f4b8e3bfd06f9e1d9ba34fc7a56421`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
