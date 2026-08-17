# Orchestration Run Summary

- Run: `db739e7071ac4cd48d42320247b92873`
- Task: `8fca77f335804ea0baf9cfd246c97b1b`
- Objective: Close P0.3 F2 in scripts/packaged-recovery-smoke.js only. Preserve exact packaged Supervisor argv ['--recovery-host']; isolate through a temporary APPDATA root, kill only the exact owned host PID without /T, then require real packaged Supervisor Once to recreate a new authenticated Recovery Host and healthy Recovery MCP. Preserve production descriptor stability and cleanup. Do not rebuild or touch dist, Scheduled Tasks, production AppData, active development runtime, tests, AGENTS.md, UI files, or volatile evidence.
- Status: **accepted**
- Started: `2026-08-17T09:50:00.116Z`
- Finished: `2026-08-17T10:00:27.125Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e91e5625ce914f1b86b6e56f498ff18e` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `80a24648525e4eac808e953ad54028c5` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 3 | `e91566a97df440dfa6bd1e4598c8aae2` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 46b3c443bdb44a99a158747b63d05791 | e91566a97df440dfa6bd1e4598c8aae2 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 9dd2363f558dad78294e3431c5b4776bdd73f3655004e4653655ef7db791c340 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13356 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 13380 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 13402 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13372 | `CHECK_FAILED` | `PROVING` |  |
| 13396 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `81`
- Chain head: `d3ea95e8cfc0fe333b9980ef064af64376813f71f7951d97c71420d22bd36c41`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
