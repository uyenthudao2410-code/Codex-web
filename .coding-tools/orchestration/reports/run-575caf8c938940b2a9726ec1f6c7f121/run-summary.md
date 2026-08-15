# Orchestration Run Summary

- Run: `575caf8c938940b2a9726ec1f6c7f121`
- Task: `7d123ba858544671a10ead575747036f`
- Objective: Add the missing focused regression suite for the already-applied internal Code Mode host-binding proxy. Prove the four allowlisted read-only bindings work, absolute/drive/parent/symlink escapes and exec/mutation/env/network-like operation names fail closed, authorized_roots do not widen Code Mode beyond the primary workspace, request/response caps fail closed, semantic match paths are revalidated, metadata remains gated with host proxy ready/worker isolation missing, and Smart-v3 remains exactly 8 tools with the unchanged contract SHA. Do not alter production source in this wave unless a test demonstrates a real defect. No restart, deploy, commit, push, provider call, or routing change.
- Status: **accepted**
- Started: `2026-08-15T03:21:39.285Z`
- Finished: `2026-08-15T03:25:29.095Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **9**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `655cd8bb38e8477d9a6c6618b69befb2` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `149f5a36988a4d08b3d7b4562ae7cfe1` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 3 | `46487869409b4f3ba6c39fb6be1ec504` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f9c9af20fbdd47cbac754517b5fc349f | 46487869409b4f3ba6c39fb6be1ec504 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 5bff450f5524e2e611a2bd7d7db361f761d6404c82ecd4664b6f9150b19a07b2 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4038 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 4055 | `deterministic` | `deterministic` | explicit_request |
| 4072 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4050 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 4067 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `da0c868c2612b43965bf8bed4bacc774800338fa4a35d0d32b1d5c6e6b87d314`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
