# Orchestration Run Summary

- Run: `4efb680c2b9e4799afc62d5ed21658ce`
- Task: `7635d4eda5f84d349ccfcb4f8eebaa71`
- Objective: Project the already-accepted proof-cache observability metrics into the existing machine-readable runtime activation benchmark snapshot. Add proof_cache_eligible, proof_cache_misses, proof_cache_miss_reasons alongside existing hits/saved_ms and update the focused snapshot test. Do not change snapshot schema_version, runtime behavior, Smart-v3/public schemas, proof reuse semantics, routing, or safety boundaries. No paid calls, restart, deploy, commit, or push.
- Status: **accepted**
- Started: `2026-08-14T15:50:46.805Z`
- Finished: `2026-08-14T15:51:16.022Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `781c285eb9ef482486f901e90826e7d6` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fc6f47d58cef432288aef5480330e975 | 781c285eb9ef482486f901e90826e7d6 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 | c4467d16dc3a9e02c64d4fd98c309e0ae5b438a3e5b71c2ea8cd3a49d552ae40 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2613 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `27acc0d199a020268c0aef2443836870768468525d86acfd8a630fb1a4b5061a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
