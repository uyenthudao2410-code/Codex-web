# Orchestration Run Summary

- Run: `3b978ca3ccb840c1aee84bc122b2a4a6`
- Task: `4bbed83a45dc4d50bd344b43f0bd6fc4`
- Objective: S2 final proof-only preflight. Locate the exact focused existing tests and source symbols needed to prove: provider_result artifact_ref wiring, orchestration_proof artifact_ref, handoff_capsule artifact_ref, build_artifact artifact_ref, bounded read_project_artifact offset/length/default/max behavior, and native image retrieval MIME plus SHA-256 integrity. The command_output lineage wave is already accepted and should be reused, not rerun. No writes, no docs, no S3. Return exact test names/commands and relevant symbols with minimal context.
- Status: **accepted**
- Started: `2026-08-20T23:53:04.247Z`
- Finished: `2026-08-20T23:56:34.346Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c5aed396c3a2494fa513ec46efb61f4f` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `765f375570f842f28ae5403d1f643378` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e4f333c16d3e4f6e860a3980a255403e | 765f375570f842f28ae5403d1f643378 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 8428b6bd89b1e3474a39e8acf19fe9b0ca13672c984b7713cae501ea21df47de | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 24581 | `deterministic` | `deterministic` | explicit_request |
| 24598 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 24592 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `99`
- Chain head: `5390ad5c46e8f2b721c12ae13fcbd904760924da26af1508dba28683191b8c51`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
