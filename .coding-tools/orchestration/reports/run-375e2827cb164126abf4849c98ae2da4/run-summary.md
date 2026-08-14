# Orchestration Run Summary

- Run: `375e2827cb164126abf4849c98ae2da4`
- Task: `a0da994fa3d84d28aecaee154c9ce324`
- Objective: Wave C: instrument resident Hub proxy gateway latency bằng bounded monotonic rolling samples per kind (mcp/heartbeat/telemetry), expose metrics() p50/p90/p99/max + status-class counts + failures, không lưu body/header/token và không thêm endpoint/transport. Bổ sung deterministic Node assertions.
- Status: **accepted**
- Started: `2026-08-14T16:20:00.920Z`
- Finished: `2026-08-14T16:21:05.400Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1fc261e8a35a4a98b07a91c16bde51c2` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | replanned |
| 2 | `85e665e182f945b6ab8025a692fe8f97` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7266e7525dff48d2946e0ca444dca424 | 85e665e182f945b6ab8025a692fe8f97 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2764 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 2774 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2768 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `2cd44ee3e8af66af11f2bc1697902e16a29d3191e2c066c8f400dc2ed7e6db51`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
