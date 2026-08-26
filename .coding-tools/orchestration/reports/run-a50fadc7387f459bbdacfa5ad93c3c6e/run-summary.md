# Orchestration Run Summary

- Run: `a50fadc7387f459bbdacfa5ad93c3c6e`
- Task: `a4e448fcd9b44567acc001cc0f30eb49`
- Objective: Continue the same health-null diagnosis by tracing how Recovery Host constructs and persists deviceIdentity/deviceInstanceId across host replacement and how RuntimeOrchestrator/runtimeDeviceIdentity compares it with the MCP child device_id. Determine whether host handoff can change expected device_id while the live MCP retains the prior device_id. Read-only only; no file or runtime mutation.
- Status: **aborted**
- Started: `2026-08-26T09:01:56.228Z`
- Finished: `2026-08-26T09:05:44.317Z`

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
| 1 | `e09353d3363a41588ad21b45669118b7` | 1 | `run_initial_objective` | `mcp_only` | `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9` | aborted |

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
- Events checked: `6`
- Chain head: `d10d87d927748ea9ad47129dbab801fbee5b9b0613e9283100aac79958973ea8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
