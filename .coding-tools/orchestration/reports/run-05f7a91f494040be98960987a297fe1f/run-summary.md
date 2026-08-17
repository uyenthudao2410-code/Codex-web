# Orchestration Run Summary

- Run: `05f7a91f494040be98960987a297fe1f`
- Task: `1aa835d317f54d0ab8f5f03f190de6bd`
- Objective: Implement and verify P0.3 F4 and F6 real-process tunnel recovery proofs only. First inspect electron/services/tunnelService.js plus the exact RecoveryPlaneService and RuntimeOrchestrator tunnel start/recovery seams. Add the smallest test-only local tunnel fixture that supports the production run/health invocation shape, opens a real loopback health listener owned by the fixture PID itself, reports JSON health, and makes no external/provider network calls. Then add F4 to tests/recovery-plane.test.js: start an isolated Recovery MCP + Recovery Tunnel through production RecoveryPlaneService using the fixture, record Recovery MCP PID and Tunnel PID, kill only the Tunnel PID, rerun the production ensure/recovery path, prove a different Tunnel PID is promoted, Recovery MCP PID is unchanged/alive, device identity and configured ports remain correct, the health port responds from the new Tunnel PID, and no duplicate/foreign listener is adopted. Add F6 to tests/runtime-lifecycle.test.js (or the narrowest existing primary runtime test file): run an isolated primary Coding MCP identity/process fixture plus primary Tunnel through the actual production tunnel recovery path, kill only the Tunnel PID, trigger the same recoverTunnelOnly/supervision path, prove a different Tunnel PID is running, the Coding MCP PID/workspace/device identity is unchanged/alive, and health/listener ownership is correct. Preserve all unrelated dirty UI files and all production source. If the existing production interfaces make this impossible without changing production code, stop with a concrete REPLAN reason instead of weakening ownership checks. Run git diff --check on only changed F4/F6 test/fixture files and node --test tests/recovery-plane.test.js tests/runtime-lifecycle.test.js. Report exact changed files and exact PASS/FAIL counts.
- Status: **accepted**
- Started: `2026-08-17T10:04:05.279Z`
- Finished: `2026-08-17T10:14:40.573Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `931a8d17ff7945748f79cf5e7b8a5108` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | replanned |
| 2 | `67882053f2034cf9830bb01ad9718c8f` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 93083bf8e9914ea8a38af25c7a137070 | 67882053f2034cf9830bb01ad9718c8f | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | ce740922f47d181784640f2cdd4099be3d2c0984314d06e5c6f365c90823b3e9 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13485 | `deterministic` | `deterministic` | explicit_request |
| 13513 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13502 | `SOL_REJECTED` | `ACCEPTING` | Reject semantic completion for F4/F6. Durable audit is content_free with files_modified=0 and no implementation delta; the execution lease had allowed_paths=[] and the workflow only reran existing tests. Although git diff --check and the focused Node suite passed, that does not satisfy the requested new real-process PID proofs for F4 Recovery Tunnel replacement and F6 primary Tunnel replacement. Replan must explicitly add scoped test-only fixture/tests (or stop with a concrete impossibility reason) while preserving unrelated UI work and without weakening ownership/listener-PID checks or changing production source absent a reproduced defect. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `f9c1971a606ad27c12af5489e30e14deebeba87aba090547b56b77d63e7c4e9e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
