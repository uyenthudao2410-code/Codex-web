# Orchestration Run Summary

- Run: `098643a972ab4ec78dd86f230cd4c87e`
- Task: `6c03e39a306945479a0150158f4c3fff`
- Objective: Diagnose the live Recovery Tunnel failure shown by the operator after configuring a distinct recoveryTunnelId. Read-only investigation only. Identify whether the failure is caused by tunnel ID/account provisioning, Runtime API Key/auth, proxy/network, tunnel-client invocation, process lifecycle, or missing recovery-specific configuration. Preserve fail-closed behavior and do not mutate source/config/runtime yet. Return the exact local evidence paths/status fields and the smallest next proof needed.
- Status: **accepted**
- Started: `2026-08-16T10:33:05.821Z`
- Finished: `2026-08-16T10:37:37.457Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `fe928148d2d44aea8c43b9b72f2459e5` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 2 | `3a35436bd9614500a7c890138902abc3` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 540226ccd1b04aecab833747344f2529 | 3a35436bd9614500a7c890138902abc3 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 44acfac8e19c658314be22e18aa5320002218aafb0aa8f455fd2dc02bfce620b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 7059 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 7053 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `179eb5ad157300a163b96251ed6b63fb344a06959da2eb0b963c551d64b03e42`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
