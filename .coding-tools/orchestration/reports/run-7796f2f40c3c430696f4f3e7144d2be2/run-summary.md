# Orchestration Run Summary

- Run: `7796f2f40c3c430696f4f3e7144d2be2`
- Task: `f5af47f6463a40cd85a6407e5af35348`
- Objective: Run the final exact-source closure proof on current committed source HEAD 9e150020a0c0829a988ffea527d5c8d82132ed65. Do not mutate source. Prove whitespace/diff integrity, repository secret guard, full Electron/Node tests, full Coding Tools MCP Python tests, Rust library tests, and targeted rustfmt for currently changed Rust surfaces. Treat any proof failure as fail-closed and report the exact failing stage. Runtime evidence dirtiness under .coding-tools is not source drift.
- Status: **aborted**
- Started: `2026-08-23T04:23:17.244Z`
- Finished: `2026-08-24T10:50:46.191Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `2ce67ce18d9242b58e444337c85f4170` | 1 | `run_initial_objective` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | replanned |
| 2 | `954a057a3fb347e18f6752ab3878d9c4` | 2 | `replan_request` | `mcp_only` | `9e150020a0c0829a988ffea527d5c8d82132ed65` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28246 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28277 | `PROOF_TIMEOUT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `118e7757214469a8292f0930ef294c2a35abd62c15c23dc310e6ad0d77179c9f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
