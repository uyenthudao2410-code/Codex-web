# Orchestration Run Summary

- Run: `e0dba795fc914a249075315f83c61d4b`
- Task: `477e66ecc84640168ddae875a9af0429`
- Objective: Natural #13: align the public task_control problem_resolution_envelope JSON schema with the exact structural contract already enforced by normalize_resolution_envelope. The public schema must reject structurally invalid envelope payloads before dispatch while accepting canonical valid payloads. Do not change runtime resolution semantics, controller authority, tool names/count, P5, activation, or Problem transition behavior.
- Status: **accepted**
- Started: `2026-09-09T23:56:02.282Z`
- Finished: `2026-09-10T00:07:24.789Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **9**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `994f2484c97f43f5a396a832c2aa5e38` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `1eaae55e73054d84baa54470c311be15` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `efb3872f49ab4edf90ef8fdf85c2e96b` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 4 | `a837206f583f4d4b811b176bc847325c` | 4 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d4f6d4ae056949bc8c009dc5dd2b2dd3 | a837206f583f4d4b811b176bc847325c | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | d6241ef3a22fa61c4322c3b505713b10faa4a4e61f7fa3cb180888fe4b6c2ef9 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 46428 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 46455 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 46493 | `deterministic` | `deterministic` | explicit_request |
| 46526 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 46443 | `CHECK_FAILED` | `PROVING` |  |
| 46481 | `CHECK_FAILED` | `PROVING` |  |
| 46514 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `141`
- Chain head: `1b349f7260049073149630b42758f636981fb048222d53431a4545401152445d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
