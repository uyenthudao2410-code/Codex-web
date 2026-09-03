# Orchestration Run Summary

- Run: `1531589e81c04475bf637c21a3d90685`
- Task: `f10e4291560f407e88782dcc7074a94f`
- Objective: Complete H0/L3 ChatWeb controller token measurement with a content-free post-turn sideband. Observe only already-parsed structured response.completed usage in the embedded ChatGPT renderer; require exact non-negative integer input/cached/output/reasoning fields, never infer missing fields or read/persist message text. Correlate the numeric receipt with the existing turn_id/trace_id to RUN/WAVE binding, send it through the existing authenticated controllerUsage MCP ingress under ChatWeb identity, and allow the immediate post-turn receipt to attach to the exact just-CHECKPOINTED accepted run while the durable controller lease remains authoritative. Preserve dedupe, unknown-not-zero, 8-tool contract, and all unrelated dirty work.
- Status: **aborted**
- Started: `2026-09-03T07:29:47.627Z`
- Finished: `2026-09-03T10:09:44.321Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0da0ae1d619f49999111e758823464dc` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `30370803440544f39c93565edd8d32d4` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `aba1d79b372b49d1bc51c560df0d5e80` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36654 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36664 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 36657 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 36675 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `5d89204049c8837cb02a72dc61baba3832a6964aafc43f7192ff0e004e5d8488`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
