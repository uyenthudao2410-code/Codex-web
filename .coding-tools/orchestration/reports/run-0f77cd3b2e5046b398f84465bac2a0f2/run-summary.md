# Orchestration Run Summary

- Run: `0f77cd3b2e5046b398f84465bac2a0f2`
- Task: `d994a9466b0b441da7c558be73d68b5e`
- Objective: Inspect the existing Execution Hub/Codex Desktop integration and identify the smallest safe extension points to add an OpenCode Go provider path for DeepSeek V4 Flash/Pro, while preserving current 8-tool smart-v3 public contract and existing Codex Desktop thin-proxy behavior. Also locate current routing/bridge code for Terra vs Sol benchmark instrumentation and the existing benchmark report to extend. No writes.
- Status: **accepted**
- Started: `2026-08-14T06:33:52.296Z`
- Finished: `2026-08-14T06:44:08.555Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `017be8b63100490aa488b49f538ef307` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `694c5d4a14f6403fb0e3089bf0ca0520` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 272ec502ab2946f5979e09a81836cf3c | 694c5d4a14f6403fb0e3089bf0ca0520 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | bfda7d0f819f5ee014456c6d3c8c2fa5833dbecee7ac084b5174e9bde5440dbb | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1404 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1418 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1411 | `SOL_REJECTED` | `ACCEPTING` | OpenCode live canary failed: {env:APPDATA} substitution produced an invalid JSONC Windows path (InvalidEscapeCharacter). Replan to make hub_proxy_stdio derive the default Electron descriptor from APPDATA when no --descriptor is supplied, then keep project opencode.json free of machine-specific path substitution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `3fb74a7135a1305e8ef256e9dfbb8392f9153fe18d6c5cf76282d2906eea328b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
