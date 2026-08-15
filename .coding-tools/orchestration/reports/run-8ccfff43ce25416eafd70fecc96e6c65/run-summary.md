# Orchestration Run Summary

- Run: `8ccfff43ce25416eafd70fecc96e6c65`
- Task: `5083c179218f4139bf3b6b63b31c3041`
- Objective: Live Wave 2A idempotency canary after runtime recovery. Dry-run only; prove same-key durable replay without writing source.
- Status: **accepted**
- Started: `2026-08-15T10:53:06.241Z`
- Finished: `2026-08-15T10:53:36.808Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `554ce036a60647c9b2b5263510eb1547` | `mcp_only` | `f64abe25a85e6abaa9fe9eeacd3665eb29a82515` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 41db49a5df22422a90c0f77fca55c710 | 554ce036a60647c9b2b5263510eb1547 | accepted | f64abe25a85e6abaa9fe9eeacd3665eb29a82515 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5290 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `81e5aaf11007ae0eb1632b27c26adb0e946b866176616e72bd637e8fb26ae7e8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
