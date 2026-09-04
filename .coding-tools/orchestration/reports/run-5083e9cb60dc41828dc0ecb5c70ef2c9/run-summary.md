# Orchestration Run Summary

- Run: `5083e9cb60dc41828dc0ecb5c70ef2c9`
- Task: `f6f9c38011694566afa20a6ef2fe1d2e`
- Objective: Final read-only live-evidence discrimination for L3 exact controller usage. For the already accepted canary trace 6a99a477000000008c206aff40665b8c / turn chatweb-trace:6a99a477000000008c206aff40665b8c, inspect only content-free repository/runtime evidence to determine whether any controller_usage event or controller-usage rejection/bridge error was observed after that ChatWeb turn. Search the host observation journal and bounded runtime evidence for this exact trace/turn and controller usage classifications. Do not mutate source or telemetry, do not use raw HTTP/MCP/stdio, do not restart/commit/push/release/deploy, and do not infer zero tokens from absence.
- Status: **aborted**
- Started: `2026-09-03T16:54:22.520Z`
- Finished: `2026-09-03T17:00:35.620Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `fa5096280f0a48c89d71113ca1088c5a` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `6`
- Chain head: `2ef8d8fb8e445106f10137ae353e1b3d3769bba938b27deb60ed4edcc57ce491`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
