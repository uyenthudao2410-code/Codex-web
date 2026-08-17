# Orchestration Run Summary

- Run: `44add57e789e4b14bcef1588f0e371b9`
- Task: `4e4cff2e57664913b09116ba88ae8bc9`
- Objective: P0.2 preflight and real Scheduled Task installation from the already fresh controlled acceptance app. Do not change source or rebuild. Require HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, acceptance root present, installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, Scheduled Task absent, supervisor root absent, healthy existing Recovery Host descriptor/process, and exactly one listener on each 18766/18767/18082/18083. Capture current Recovery Host PID+instance as the immutable baseline for this installed-session acceptance. Then invoke the installed supervisor -Action Install with installed app executable/AppRoot/Packaged and verify task structure: same current user, Interactive logon, Limited run level, fixed PowerShell action referencing %LOCALAPPDATA%\WebMcpRecoverySupervisor\recovery-supervisor.ps1 with -Action Run, two triggers, manifest mode packaged, manifest arguments exactly ['--recovery-host'], manifest executable/hash match installed app, installed supervisor copy hash exact. Return only content-free identities and task structure, never descriptor token.
- Status: **accepted**
- Started: `2026-08-17T08:48:09.479Z`
- Finished: `2026-08-17T08:50:19.788Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `756902de176d4468acf62430864595a6` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 2 | `78a350d948404e688623539764c0c0cf` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 3 | `730ddc9e526b4c4981ca1c82e257196c` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 803a6e0d1a234fcd82857059755f03d2 | 730ddc9e526b4c4981ca1c82e257196c | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 525711ac2ee76063fe9ebb69f821cbb1ad08bbad19f1856273d89778ed373bcc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12758 | `deterministic` | `deterministic` | explicit_request |
| 12782 | `deterministic` | `deterministic` | explicit_request |
| 12801 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 12774 | `CHECK_FAILED` | `PROVING` |  |
| 12793 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `52ffb533cbbd15df0a7b36408c47f0603635ea682fdea9e7d8720b85910e4a29`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
