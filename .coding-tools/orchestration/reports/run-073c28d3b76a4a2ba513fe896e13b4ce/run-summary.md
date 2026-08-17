# Orchestration Run Summary

- Run: `073c28d3b76a4a2ba513fe896e13b4ce`
- Task: `225601286f6849de87bcf7047e28cfec`
- Objective: Diagnose the recovery path while the foreground Electron/UI is intentionally left OFF. Do not run any start/restart/kill command and do not manually wake the app. Inspect source and persisted orchestration/runtime evidence only. Determine whether Recovery Supervisor/Recovery Host is designed to auto-reconnect or relaunch the foreground app after it is stopped, what trigger/cadence/ownership conditions control that behavior, and whether the current code contains a defect that would explain the app not reopening automatically after the previous shutdown. Focus on recovery supervisor, recovery host, recovery plane, runtime restart ticket handling, and tests. If a concrete defect is found, return a minimal patch plan but do not execute the patch yet.
- Status: **accepted**
- Started: `2026-08-17T10:27:26.742Z`
- Finished: `2026-08-17T10:43:53.434Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `4782b1aa624f4cf3baf66467586bce1c` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `01c3b28b9387429798d1b0a270364f2a` | `bounded_candidate` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 3 | `e43ad3916ac6462b97e014959e9564b4` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 4 | `2fc0162c843f45b0868d0e93fde3c108` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 67a59093039d4d04ad8ffe28b76be28d | 2fc0162c843f45b0868d0e93fde3c108 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 7bcb572fa7191c6335ad201f739d2fb5569e41c618dfc74a411ddd3b1854a14b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13571 | `luna` | `luna` | explicit_request |
| 13583 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 13597 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13561 | `MODE_ROUTE_MISMATCH` | `PREFLIGHT` |  |
| 13577 | `PROMPT_TOO_LARGE` | `ROUTED` |  |
| 13590 | `SOL_REJECTED` | `ACCEPTING` | Acceptance review found a concrete current-user-case defect: after Recovery Host replacement while the Electron UI is already off, uiRegistration is empty in the new host and the watchdog remains untracked forever. Replan must arm UI recovery by default when there is no durable explicit operator suppression, allow an initial UI re-registration grace window, then use the existing trusted bounded launcher if no UI appears. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `59`
- Chain head: `a4ce1f7f9a7e866bec820b68ffccf4fbe374d690d6003df20d62ba30654d07ab`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
