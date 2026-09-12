# Orchestration Run Summary

- Run: `e94e9cadac0b40708f2274fa24ec28fb`
- Task: `b796ce430aeb435c9a8c57b002f8ab51`
- Objective: Natural live validation after the post-checkpoint runtime activation for Problem prl-8a57cc01ad8abd9f56a14c8bd605229d revision 1. On the currently loaded runtime, run the current stage-latency attribution reporter against the exact current source HEAD and then carry this real diagnostic RUN through the normal EOCL acceptance boundary without source mutation. The purpose is to observe whether the live acceptance path emits same-clock acceptance-start, controller-processing, and acceptance-wait evidence. Preserve unknown on missing/cross-clock evidence; do not backfill history, do not edit source, and do not claim Problem resolution from the diagnostic alone.
- Status: **accepted**
- Started: `2026-09-12T06:45:31.622Z`
- Finished: `2026-09-12T06:46:14.597Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `19d9574db27547faa36ed20e6af3a1a2` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4febd54de4f146129d20f276eadf2ed7 | 19d9574db27547faa36ed20e6af3a1a2 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 03a922ff8127a3fcf675e5654299bfc4fccb39c58813c7a5bed7ab4138d02303 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50378 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `29cf970eef3d9496a7506cd71983271b8256abea240eec3526e364d388d1336c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
