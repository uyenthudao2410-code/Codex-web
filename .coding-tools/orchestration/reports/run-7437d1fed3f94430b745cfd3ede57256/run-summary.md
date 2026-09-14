# Orchestration Run Summary

- Run: `7437d1fed3f94430b745cfd3ede57256`
- Task: `9b521f6a9867489ab84049316f0c89d2`
- Objective: Complete the current diagnosis/preparation wave for canonical C01 on the already-bound RUN 0bc471f379924d81be114112733dc681 / WAVE b88d57aaf0d642c7a6bc911211c7fda9. Based on the source already localized in this wave, determine and report with exact file/function references: (1) the installed/direct/logon cold-start owner and startup chain, distinct from dev refresh; (2) which code path may create a fresh activation epoch when the previous managed MCP/Recovery Host/Tunnel process is absent; (3) whether terminal READY/READY_COMMITTED/FAILED state can incorrectly spawn a child and what guards prevent it; (4) whether current source already satisfies the source-level behavior or the smallest exact source/test delta still required before installed/logon and reboot evidence; (5) a bounded next-wave plan and deterministic oracle. Read-only diagnosis only: no source mutation, restart, reboot, process termination, package/install, commit/push/release, state deletion, or Goal-pagination/P5/public tool contract changes. Preserve unrelated dirty work.
- Status: **aborted**
- Started: `2026-09-14T11:40:12.495Z`
- Finished: `2026-09-14T11:41:21.800Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d9f6fa02bb964d49b7b31d4755a0ccd0` | 1 | `run_initial_objective` | `mcp_only` | `ae04947d5969e9ee92bf1fe7532bf30e186f8280` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 54735 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 54741 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `40119a67f9570b54d99a09a7553186eb979220685104a2c5127e3ab721e23acf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
