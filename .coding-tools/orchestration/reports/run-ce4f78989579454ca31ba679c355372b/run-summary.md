# Orchestration Run Summary

- Run: `ce4f78989579454ca31ba679c355372b`
- Task: `68473624dc5f40cbaf2b8571d95a15bf`
- Objective: Fix the live final-acceptance publisher scope bug demonstrated after MCP reconnect: Runtime dispatch records agent_workflow results, but TaskStateStore currently reads only payload.affected_files while the real agent_workflow result places them at payload.execution.affected_files. Preserve backward compatibility with top-level affected_files for other/current callers. Update the existing regression to use the actual nested agent_workflow payload shape and update the direct runtime acceptance fixture similarly. Modify only resources/coding-tools-mcp/coding_tools_mcp/task_state.py and resources/coding-tools-mcp/tests/test_task_state_and_build.py. Preserve all unrelated dirty WIP. Prove with the focused task-state/orchestration tests and module-size guard; do not restart runtime in this wave.
- Status: **active**
- Started: `2026-08-16T06:15:10.640Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6c46722083874fa88ad36eb41b594f08` | `mcp_only` | `597170860118a847b7e8a6f06903c37da8432d82` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 6078 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `0992f914c49a87385229acc590722e160dbe3b19dbb7c3fbfe9b18cb763e7d83`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
