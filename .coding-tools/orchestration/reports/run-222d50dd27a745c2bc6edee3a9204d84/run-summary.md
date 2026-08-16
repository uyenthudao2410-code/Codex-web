# Orchestration Run Summary

- Run: `222d50dd27a745c2bc6edee3a9204d84`
- Task: `0a9f536b635e418fbfb620d738a2bebb`
- Objective: Move the Recovery Tunnel configuration UI out of Settings and into Connections, directly alongside the primary Tunnel ID in the OpenAI Tunnel identity panel. Preserve existing Recovery Tunnel backend, telemetry, header status, duplicate-ID validation, save behavior, and OpenAI tunnel management link. Simplify the Connections UX so primary and recovery tunnel IDs are configured together; remove the standalone Recovery Tunnel card from Settings. Preserve unrelated concurrent work.
- Status: **accepted**
- Started: `2026-08-16T10:26:22.627Z`
- Finished: `2026-08-16T10:29:50.473Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6de5d7ab76cf4b08a840d8abd21c3989` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 1a1bad8c6b504d91849599b020bd033c | 6de5d7ab76cf4b08a840d8abd21c3989 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | aa6491cbf818a13b71cf230420e45881672e7cb0845e9290f461d17b4c674208 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 7000 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `10c0f256f43c8cde79dff0d928ec5b5863d7ea3a388889bdb47e46aa56ef04d8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
