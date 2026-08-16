# Orchestration Run Summary

- Run: `ad6f638a17984968b8762a033e4b9f39`
- Task: `caf17154e89146eab1c8922bde8ea74c`
- Objective: Verify the current smart-v3 public tool names directly from Python source. Read-only; return only relevant source evidence and do not mutate runtime state.
- Status: **accepted**
- Started: `2026-08-16T10:41:40.900Z`
- Finished: `2026-08-16T10:45:22.013Z`

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
| 1 | `2086a5cf44b047c3a0faf6cadd5b11a9` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | replanned |
| 2 | `243281a552e14530bd0309e337a8d197` | `mcp_only` | `415cb658f43cbd1d2456f65bf5649ed52b87ab25` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 53f3a83632b34ce1a001d8f652445fcd | 243281a552e14530bd0309e337a8d197 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | c3a290e1bd14171d466913c64d7425ae000cef4d67ea0b22bbb526d278ac353c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 7159 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 7152 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `14f7e8085d31c2cd61ba30065da287423b87439d89bee54536ff1c29ad354482`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
