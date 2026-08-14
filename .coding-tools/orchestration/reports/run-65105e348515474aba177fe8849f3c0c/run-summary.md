# Orchestration Run Summary

- Run: `65105e348515474aba177fe8849f3c0c`
- Task: `869da05281a64127844b2c6b1779c7f6`
- Objective: Live zero-billing OpenCode Flash canary preflight only. Run the checkpointed operator canary in --preflight mode while this orchestration wave is in an eligible proving state. Require authenticated live MCP health to match this workspace, Smart-v3, 8 tools, non-empty runtime instance, and current active run/wave. The preflight itself must report provider_dispatches=0. Do not invoke provider_dispatch, do not run OpenCode inference, do not mutate source/settings/services/Git, and do not commit/push/restart/release/deploy.
- Status: **aborted**
- Started: `2026-08-14T12:39:04.713Z`
- Finished: `2026-08-14T12:41:38.721Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `0411cba938ab4b1ca9b9ce17c915db55` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1980 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `b5ea1e41cad7b494f395297b7cc26e239e1facf4acf1dc6f900b1d9f7392c369`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
