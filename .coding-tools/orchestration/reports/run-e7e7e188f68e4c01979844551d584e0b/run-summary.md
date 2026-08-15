# Orchestration Run Summary

- Run: `e7e7e188f68e4c01979844551d584e0b`
- Task: `2e2a6240f8b34145841228ba76f8092c`
- Objective: P5A implement the authenticated model-hidden Rust native semantic LSP bridge. Add one exact connector-internal route that accepts only project credential auth for the exact grant plus project:read, verifies a SHA-256 of the caller workspace against the connector's canonical executor root, accepts only bounded workspace-symbol queries, dispatches only the existing read-only workspace_symbols ToolKernel operation against context.executor_project, and returns only normalized project-relative symbol matches. Keep the route out of CAPABILITY_NAMES/OpenAPI/MCP and keep generic /api/tools/call denied. Add focused tests for exact-route hard gate, hidden route, bootstrap/wrong-grant/wrong-workspace rejection, unavailable LSP capability, and happy-path typed LSP normalization. Do not touch Routing-v2 gates, restart, deploy, call providers, commit, or push.
- Status: **active**
- Started: `2026-08-14T22:41:30.938Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `49cb2624ca874ae7a60868baa1283c10` | `mcp_only` | `e45bed968bee6db46bb3041de179cbcf23e3906b` | replanned |
| 2 | `b405c5c2b1e14daab57d039173588420` | `mcp_only` | `e45bed968bee6db46bb3041de179cbcf23e3906b` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3418 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3428 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3422 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 3436 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `66cb5d347876f7f641a0d5742f25fbe54f4dbec0a2cbe002be1caf3f458dc171`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
