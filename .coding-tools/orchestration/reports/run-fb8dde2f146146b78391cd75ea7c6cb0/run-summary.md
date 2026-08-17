# Orchestration Run Summary

- Run: `fb8dde2f146146b78391cd75ea7c6cb0`
- Task: `eb87952994444b9d8c18f00d3bd4ee11`
- Objective: Map the living-plan P0.3 F1-F9 matrix to exact current proof strength without changing source. For each F1-F9, identify the strongest exact test/script and whether it is real process, isolated fixture, deterministic unit, source/static assertion, packaged/installed acceptance, or external-only. Pay particular attention to F2 Recovery Host PID exit -> Supervisor recreation; F4 Recovery Tunnel PID exit -> new Tunnel PID while Recovery MCP PID stays; F5 primary Coding MCP PID exit -> current RuntimeOrchestrator policy and no foreign adoption; F6 primary Tunnel PID exit -> tunnel-only recovery with Coding MCP PID preserved; F7 stale Recovery Host lock/descriptor replacement; F8 foreign/live listener/owner fail-closed; F1 and accepted F3/F9 evidence. Identify the smallest genuine test additions needed to meet docs/PRODUCTION_CLOSURE_ROLLOUT.md without external tunnel/provider credentials and without touching the active development runtime. Also locate any existing packaged/isolated recovery smoke harness that can cover F2/F4/F6.
- Status: **accepted**
- Started: `2026-08-17T09:41:19.845Z`
- Finished: `2026-08-17T09:48:45.660Z`

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
| 1 | `1bf7d976ea534024831b87bf4812cdd5` | `mcp_only` | `885260b404c2c64df1b1afa835963045ac55dbf6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 1ab485ff88ce445fb6cf37d50ef32a98 | 1bf7d976ea534024831b87bf4812cdd5 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 3993de7151e27da2a922fe0a1a28d25e17e0acce527a9cadd36178e74fb55f67 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13310 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `10740a0a039045339cb38b4083098020b12e4af03a74d86dc6ab2cd045638b95`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
