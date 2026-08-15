# Orchestration Run Summary

- Run: `0ff441bc5e914e77b5c3217b0b9dee72`
- Task: `857ca35bac0947b4b85d92a7810fcaf0`
- Objective: Broad P1 acceptance proof on the exact current dirty worktree: run the repository-wide Node/Electron test suite and the full Python MCP suite via npm run test:all. Proof-only; do not mutate source, restart runtime, invoke models, or create benchmark workload. P1 spans, host-visible telemetry, replay harness, reporter, and all prior P0 behavior must remain compatible.
- Status: **accepted**
- Started: `2026-08-15T08:14:56.155Z`
- Finished: `2026-08-15T08:20:04.244Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2d47fb68128d44edba88c55370dab881` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 03907384c41b4a91b74570279d265a13 | 2d47fb68128d44edba88c55370dab881 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 610c5ef71e1326619eff8ae96d1167df4cd8cc4036a828addb93fb059305826b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4972 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `207f315c484ef763540031187bc14e4431066b94d4f934ad7cdeefecb7775400`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
