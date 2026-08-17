# Orchestration Run Summary

- Run: `a5b1f4933d574cc390046a92a60987ae`
- Task: `b7b9aa579ee34a51b103e17ae5951821`
- Objective: Verify and EOCL-record the already-applied dedicated P0.3 F1/F7/F8 acceptance without mutating any additional files. New F8 evidence is limited to tests/recovery-plane.test.js and tests/runtime-lifecycle.test.js. F1 evidence is the existing real Electron process integration in tests/integration/recovery-host-process.test.js. F7 evidence is the existing live-owner/dead-stale-owner lock test in tests/recovery-host.test.js. Acceptance requires: Recovery Plane rejects a genuinely live foreign or unverified owner with typed errors while leaving the PID alive; RuntimeOrchestrator defers a genuinely live recorded MCP PID when health is unavailable and calls no MCP-only recovery, Tunnel-only recovery, or full restart at the first fail-closed boundary; stale dead Recovery Host lock is reclaimable while live lock owner remains protected; real Electron client kill/reattach preserves Recovery Host runtime ownership. Do not modify production source, renderer/UI files, provider traffic, live production processes, or delivery state.
- Status: **accepted**
- Started: `2026-08-17T11:21:39.702Z`
- Finished: `2026-08-17T11:23:03.734Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3d633befc4e44bd386096509172cfc58` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `da61a770987e41768605b9b819ce7d47` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c0d1a0aa08684be6b1d82909490d11a8 | da61a770987e41768605b9b819ce7d47 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | a202cfb506558ae4df1a5949b17492822b6f89ece35427808ebeeb80283bcb1b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13803 | `deterministic` | `deterministic` | explicit_request |
| 13831 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13817 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 13823 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `7a26d59bc6837401dc9a8d119b0ea1d9200e0f339347c52d2f31ef07c8a9883a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
