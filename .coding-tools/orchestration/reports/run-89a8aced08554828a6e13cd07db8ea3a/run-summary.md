# Orchestration Run Summary

- Run: `89a8aced08554828a6e13cd07db8ea3a`
- Task: `12b75b8d7da94d6ea8c91e53c57c1404`
- Objective: Map and close P0.3 fault-matrix cases F4 and F6 exactly as defined by docs/PRODUCTION_CLOSURE_ROLLOUT.md. Identify the production Recovery Tunnel and primary Tunnel lifecycle/restart code paths and existing tests. Design the smallest test-only real-process fixture that runs under the production services without contacting an external provider: kill Recovery Tunnel and require a new tunnel PID while Recovery MCP PID remains unchanged; kill primary Tunnel and require a new tunnel PID while Coding MCP PID remains unchanged. Preserve device identity, ports, descriptors, fail-closed ownership, and unrelated UI/local changes. Do not modify production code unless a reproducible product defect is found.
- Status: **active**
- Started: `2026-08-17T10:00:45.715Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `8d5f8d5ff17e4c768bd8a78be16173d2` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `1bc5c1b9b3154b08822ad854dee0d635` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13444 | `deterministic` | `deterministic` | explicit_request |
| 13463 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13456 | `SOL_REJECTED` | `ACCEPTING` | Wave produced zero modified files and therefore did not satisfy the user's requested visible UI fix. The screenshot still requires a non-collapsing Executive Summary, readable vertical Execution Hub layout, and materially larger typography. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `49f3c52210e5191be4a1a33ef6f9f160f0978d72b73d4a275740bd521811e6f4`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
