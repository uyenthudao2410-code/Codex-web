# Orchestration Run Summary

- Run: `153e80bfb2b4449eb502cd340ade89c5`
- Task: `2e3450cbae64459fbf6fc22aa1e4a876`
- Objective: Apply the manually localized deterministic multi-provider Execution Hub patch after Terra timed out. This is the same user-visible scope, but no model cascade: explicit proxy identity for Codex Desktop/OpenCode, strict gateway allowlist, OpenCode worker registration, OpenCode config identity, and truthful nine-node router UI with focused tests.
- Status: **accepted**
- Started: `2026-08-14T07:12:09.673Z`
- Finished: `2026-08-14T07:19:17.396Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f73b4ba1cdb5454fac4b06799c3b306c` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `2533e69eb18a44b2b4fa939850b1efb5` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 3 | `b56b0b4437fd41df93113ddbd3275357` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b88881ae60bd445f85abea2709416f46 | b56b0b4437fd41df93113ddbd3275357 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | a3a6c2e7090df8faba34571fc85c76a9201c3b66e3337e2603190c445612ed50 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1474 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1485 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1496 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1478 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 1489 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `c24f0cb51295336ea2d378cc24c3c26a75a772ae699c2e5ef611ce67bc1cc0f7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
