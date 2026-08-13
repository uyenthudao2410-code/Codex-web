# Orchestration Run Summary

- Run: `d4c805e732dd4e61a1d2c56b9052a3e8`
- Task: `01eb93b741cd46d1a85197d201c8e9dc`
- Objective: Diagnose and fix the Windows CI failures on clean HEAD deb03fc5 without touching the primary dirty worktree. Failures show Windows temp paths using 8.3 short USERPROFILE/temp aliases resolve to canonical long/verbatim paths and are rejected as credential root drift; one generated-key recovery test also observes a different key. Preserve secret-path safety while treating Windows-equivalent canonical paths as identical. Use the smallest focused fix and proof.
- Status: **active**
- Started: `2026-08-13T06:03:52.742Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c3b069a064f14840b1744fc3626a79fc` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | replanned |
| 2 | `e31e2f14af8143aab9d3736047c4da4b` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 101 | `auto` | `deterministic` | caller_supplied_change_set |
| 114 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 109 | `CHECK_FAILED` | `PROVING` |  |
| 121 | `PROOF_TIMEOUT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `470f6404f4363a9b1a9246b2768d0b50d1e15da48411c12a1bc3f6fef86ee041`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
