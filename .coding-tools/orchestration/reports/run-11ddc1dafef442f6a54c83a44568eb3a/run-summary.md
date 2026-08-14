# Orchestration Run Summary

- Run: `11ddc1dafef442f6a54c83a44568eb3a`
- Task: `b9f932bf6c864d458fa7d99a519b74bf`
- Objective: Fix only `tmp/execution-hub-benchmark/capacity-luna/case.py` so remaining_capacity(limit, used) returns limit-used when positive and 0 otherwise. Do not modify `tmp/execution-hub-benchmark/capacity-luna/test_case.py`. Deterministic oracle: `python tmp/execution-hub-benchmark/capacity-luna/test_case.py`. Localized strong-oracle Luna benchmark only.
- Status: **accepted**
- Started: `2026-08-14T06:16:33.192Z`
- Finished: `2026-08-14T06:18:11.137Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `debf7d6fb8c24fee9c88656d85d355a8` | `bounded_candidate` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6cc20619421045149680bec4e83cf7c0 | debf7d6fb8c24fee9c88656d85d355a8 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | ddc3954651232499ed78ce4be76b296c2b4e785fa2b4ff05a525a7fe6dc4b0eb | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1350 | `luna` | `luna` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `3d676b0847a2b308ab0bdab0062f252e6b2bd823e70d53488623835a8c2901c2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
