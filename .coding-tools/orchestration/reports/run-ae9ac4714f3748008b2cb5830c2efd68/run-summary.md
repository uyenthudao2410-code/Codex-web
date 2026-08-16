# Orchestration Run Summary

- Run: `ae9ac4714f3748008b2cb5830c2efd68`
- Task: `7df04716bb81471199354f037394d316`
- Objective: Locate the actual launcher/owner of the live internal cmd.exe -> node.exe service without assuming class or file names. Search the whole repository for the configured native LSP provider identifier and Node/LSP launch literals, plus the controlled runtime restart implementation. Read-only only.
- Status: **accepted**
- Started: `2026-08-16T14:11:06.334Z`
- Finished: `2026-08-16T14:19:09.933Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `73f2b490b00f4bb39f4435279d6ff662` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `2092ea6b706b4c96bd3828ffaba170c9` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 3 | `8e4c99048b214ac69ca1abde7e33a743` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 4 | `cfa66b5cb5e84555829a0582f37f49c7` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3b78b19baf3a42a28162d2869324ca93 | cfa66b5cb5e84555829a0582f37f49c7 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 7d8e2aef1d8c4ca8e70a2527128f94dd84ff09a53113db6ded82fa677b9a7464 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8594 | `deterministic` | `deterministic` | explicit_request |
| 8610 | `deterministic` | `deterministic` | explicit_request |
| 8632 | `deterministic` | `deterministic` | explicit_request |
| 8650 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8604 | `INVALID_ARGUMENT` | `PROVING` |  |
| 8626 | `CHECK_FAILED` | `PROVING` |  |
| 8644 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `27fd9543ea084700b9e57ce7a42d81aaf8f80eb53ce9c0d7f1f4e553d242c9af`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
