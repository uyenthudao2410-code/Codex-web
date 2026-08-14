# Orchestration Run Summary

- Run: `fd693ed40c41493283b83ece23bb4eb6`
- Task: `8b703013ca274221a81d88d0afa0ac88`
- Objective: Add focused Execution Hub fault/E2E release tests only. Prove: ChatWeb and Codex Desktop logical identities use one shared HTTP Runtime/ledger while keeping independent cursors; Desktop cannot steal a live ChatWeb controller but explicit transfer increments fencing and stale ChatWeb semantic acceptance is rejected; an initialized authenticated MCP session id from Runtime A is accepted as an alias after Runtime A stops and Runtime B starts on the same workspace, while durable task/run/capsule survive and the response rotates to Runtime B's session id. Do not change production code unless the test exposes a real defect.
- Status: **accepted**
- Started: `2026-08-14T05:36:28.032Z`
- Finished: `2026-08-14T05:39:23.465Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `53b82fb4575a4581a20c31e04bbd5121` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `43951ac93c4544e38fa89efea2059e5e` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 3 | `27744d551a6343de864b3ea6fa9d58d3` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fda16dc2bbe74f36bd570b8169b43999 | 27744d551a6343de864b3ea6fa9d58d3 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 528e9155bd53ea86718bde388d2450e7b432d53eaaa1c47ac32988c0ae27bcb2 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1152 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1164 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1176 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1159 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 1171 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `13f5e9d955cd4233e4a623d935e01445a670549a793123781103d28477da3877`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
