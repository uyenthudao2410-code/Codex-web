# Orchestration Run Summary

- Run: `fe863a45563b4725af4804ecf05f8a03`
- Task: `141920fe0a204fd6912ac3966e74aeef`
- Objective: Natural #8: fix the embedded token-dashboard double-poll defect. The main manager parent and the embedded token-dashboard child both load renderer/control-center.js, whose unconditional initial refresh plus pollControlCenter loop independently call lightweightSnapshot/liveOrchestration. Make embedded=1 same-origin child mode passive: consume the parent's coding-tools:overview-pulse and relay coding-tools:overview-refresh-request back to the parent without starting its own Control Center poll loop. Standalone behavior and fail-safe fallback must remain unchanged. Preserve all existing dirty WIP and do not touch renderer/dashboard.js, renderer/index.html, or renderer/token-dashboard.html.
- Status: **accepted**
- Started: `2026-09-09T11:51:09.523Z`
- Finished: `2026-09-09T12:23:28.615Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `576f0bfc74284a9a8001e34958fa4a69` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `9895cded293c4d8685753dcd1839baaa` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 78a25177a2ff4c12b23d4f14324cebfc | 9895cded293c4d8685753dcd1839baaa | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 08a6a81a1dbf450302cd85a39b536fd30dbff4cfb8a5b56a99bb841e9204165e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 45712 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 45746 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 45737 | `SOL_REJECTED` | `ACCEPTING` | Reject this Natural #8 completion report as a failed no-write implementation attempt. The report itself records WRITE_SET_EXPANSION_REQUIRED, modified_files=[], proof_ids=[], and no acceptance artifacts. Preserve the failed attempt in history and allow a same-RUN replan; do not classify it as technical success. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `a8c726e07892fb2fd0bd94e4731986b0e599334e455be54e447c87c500aab371`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
