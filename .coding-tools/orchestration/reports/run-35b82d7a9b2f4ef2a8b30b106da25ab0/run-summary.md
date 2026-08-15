# Orchestration Run Summary

- Run: `35b82d7a9b2f4ef2a8b30b106da25ab0`
- Task: `043bdacd982548d28620844b11a1984f`
- Objective: P1 organic ChatWeb canary after controlled Electron/runtime activation. Create one exact EOCL run for this user turn, exercise only read-only evaluation-plane reporting, and preserve fail-closed behavior: do not modify source, do not restart, do not ACK coordination messages, do not route models, do not synthesize or manually assign host turn identity, and do not infer correlation by timestamp. The acceptance oracle is that the exact run is explicitly linked to the organic host turn by stable content-free identity and the evaluation reporter can prove explicit_host_run_identity_present.
- Status: **accepted**
- Started: `2026-08-15T09:54:09.879Z`
- Finished: `2026-08-15T09:56:50.932Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `b8401e1666a142dcb14130dd01801fd4` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f8d2cbdd07344ac8a214846ae5893d5a | b8401e1666a142dcb14130dd01801fd4 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 8f2077f60b4591fa38a66a7e97da438e312ecd681a22c212f6e86a639367574b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5155 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `16`
- Chain head: `ddf1edef67a98e8e252d8d1d2f88bff786b7f4f7da2132207e2ff5a575bce4b1`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
