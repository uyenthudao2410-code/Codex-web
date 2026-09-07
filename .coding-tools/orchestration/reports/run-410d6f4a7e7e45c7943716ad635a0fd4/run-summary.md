# Orchestration Run Summary

- Run: `410d6f4a7e7e45c7943716ad635a0fd4`
- Task: `0d353882b71b4bd38910fc7a8f27e60f`
- Objective: Audit the current Windows package composition for correctness, startup cost, and installed footprint. Inspect package.json plus any electron-builder configuration and package-smoke scripts. Determine exactly which repository trees are copied into app.asar/extraResources, whether coding-tools-mcp is duplicated, whether tests/docs/caches/dev artifacts are shipped, and whether the packaged MCP/tool schema can drift from current source. Propose the smallest package-only exclusions that preserve packaged offline startup, Recovery Host, Coding MCP, tunnel/native semantic support and Python dependencies. Do not mutate. Return current build input rules and the exact parity assertions needed in packaged-recovery-smoke.
- Status: **active**
- Started: `2026-09-06T05:53:02.412Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8592e28c0f4d4b5b8d4bf0c304819bbe` | 1 | `run_initial_objective` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `7`
- Chain head: `ec635c956b087121e602c7ce6f0dd0d8d7bacacda9d8a9d87276c2c4e23fa283`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
