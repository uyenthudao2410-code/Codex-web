# Orchestration Run Summary

- Run: `5c52b7f810ad474a9a5f3ba92873ab80`
- Task: `28ed99bfebe64640b966afa45d56e4d5`
- Objective: Fix the confirmed MCP 2026-07-28 stateless cross-tab/default projection leak. Modern stateless requests currently use process-global control_runtime with empty execution_context_id, causing ContextualTaskStateStore and exec_command/task projection to fall back to the global task/run. Implement an application-layer opaque task_context_id carried by tool calls: every modern request must get a nonempty isolated execution scope; supplied task_context_id must deterministically restore the same scope; missing task_context_id must mint a new isolated context rather than inherit global state; strip the common handle before business-tool validation/dispatch as needed; return the handle in modern results so clients can reuse it. Preserve legacy 2025 session behavior, workspace isolation, operator-report latch, accepted unrelated usage_events.py changes, and exactly 8 smart-v3 tools. Do not open P5. Prepare only; no mutation yet.
- Status: **accepted**
- Started: `2026-08-19T08:43:16.290Z`
- Finished: `2026-08-19T08:52:19.991Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `0e5d45be106347178bda384eb43513ec` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 2 | `a48da7ed0b4d4065acdf3c522b988f1b` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 3 | `53089bd8aa994af99a2d055e0cf78398` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 238634314e1c4c96b7c59c1668ed9ae6 | 53089bd8aa994af99a2d055e0cf78398 | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | 515c324d22c4d571313cba44ba2a96f92c4dfda14477d15b1f3364e2cc22bab8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 20970 | `deterministic` | `deterministic` | explicit_request |
| 20992 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21023 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 20985 | `SOL_REJECTED` | `ACCEPTING` | Reject no-op proof: focused tests passed but agent_workflow reported affected_files=[] and patch_results=[], and an explicit git diff of mcp_http_handler.py, tool_schema.py, and test_stateless_http_2026.py is empty. The confirmed stateless global-projection bug is therefore still unfixed. Replan must apply an explicit source patch before re-running proof; do not reuse proof 88a4e54872274bd7983bbeb5a4254d90 as acceptance evidence. |
| 21006 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `25a938ad238fc51fc4cdafb1ad759cf4fd458a4ffe41cde30fb82211eed90cc6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
