# Orchestration Run Summary

- Run: `1151d304b5864708ad6f694d9fd91b6c`
- Task: `0d5200a54dcb47cc99378cd10ac1a79a`
- Objective: Execute P0.2 installed Windows Recovery Supervisor current-session acceptance only on the controlled acceptance installation. Exact source HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117; exact installer SHA-256 0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879; expected installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420. Immutable before-state Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Replace only %LOCALAPPDATA%\WebMcpAcceptance-0.3.4, install the same-user Limited WebMCP Recovery Supervisor Scheduled Task from the installed package, prove continuous healthy with the exact same Recovery Host, stop task and prove installed Action Once observes the same host with no spawn, restart and re-prove continuous healthy, prove listener/device coherence, then uninstall the Scheduled Task/supervisor and prove rollback. Never kill or replace the active development Recovery Host/MCP/Tunnel. Do not infer reboot/logon persistence. No source changes and no rebuild.
- Status: **accepted**
- Started: `2026-08-17T08:43:43.062Z`
- Finished: `2026-08-17T08:45:21.554Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `0155151d6cd74afa94a1115460aa3b44` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 2 | `fc5cc270eec8419b93c57e78b2871d0f` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 32d85add08a74a33a16265c79d8de68a | fc5cc270eec8419b93c57e78b2871d0f | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 1257c10eb59c8e351a11d939a16dbe4c19d6ce212fac80a9b0681c8d9faf1f7c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12701 | `deterministic` | `deterministic` | explicit_request |
| 12720 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 12712 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `fd740e375db743295902c880e2a0c98584398a7287444f946ff9e9168d34c37f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
