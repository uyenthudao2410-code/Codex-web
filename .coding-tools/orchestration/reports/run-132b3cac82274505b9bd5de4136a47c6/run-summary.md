# Orchestration Run Summary

- Run: `132b3cac82274505b9bd5de4136a47c6`
- Task: `eef9015c5071492a913e0c18644a3cc4`
- Objective: Identify which TOML section owns the localhost/127.0.0.1 base_url without exposing the secret path token, and confirm whether the configured provider is currently actionable. No mutation.
- Status: **accepted**
- Started: `2026-08-15T07:42:47.803Z`
- Finished: `2026-08-15T07:43:09.629Z`

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
| 1 | `808ff4ed5f0b45aa88abcd18588cda39` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4f43461eeeba47f896ef77f3e963ef23 | 808ff4ed5f0b45aa88abcd18588cda39 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 998bd2bf12a795f0394b65295c0e6668ad2fca42bacdb4e73bd0f5711f8d2bb4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4744 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `17`
- Chain head: `40a20fe5fbe7e169922805a2496708c21d30f6614f489dd4f6cc98b8a3373351`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
