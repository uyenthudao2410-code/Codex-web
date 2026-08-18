# Orchestration Run Summary

- Run: `bb477fc737fd40038823bd20ecc2cc49`
- Task: `3c4a6303e0d7416fa65dc3e8792138b2`
- Objective: P3 activation preflight only: rebuild exact-HEAD webcodex-server and webcodex-runner, verify both binary versions carry current Git HEAD bc17700e, then run scripts/e2e_server_first_snapshot_ws.ps1 as a real-process loopback SourceSnapshot server-first dispatch/fallback mechanism canary. Do not modify product source, do not create representative evaluation tags, and do not interpret this canary as P3 efficacy evidence.
- Status: **accepted**
- Started: `2026-08-17T20:33:50.478Z`
- Finished: `2026-08-17T23:26:11.129Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f9e2ed6273a0481eb8ee0e4f09a9f9ee` | `mcp_only` | `bc17700e475ce74c96a9547117aade58823f0811` | replanned |
| 2 | `32196acc7f3b4e31adc7cc330b24dcca` | `mcp_only` | `bc17700e475ce74c96a9547117aade58823f0811` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 95ac76166a794201982f59e3f7b804d0 | 32196acc7f3b4e31adc7cc330b24dcca | accepted | bc17700e475ce74c96a9547117aade58823f0811 | e03f61f91a750786973c00e755d351993f841675f94ea4f980e063c0d3a5465f | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15836 | `deterministic` | `deterministic` | explicit_request |
| 15855 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 15847 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `6f11d1d0e8be75c080bd2bba6a64cfe15d85ee89238cf796040bd1c0bf8dcff5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
