# Orchestration Run Summary

- Run: `ff388faf4a8a480cb3c9becb518aeaed`
- Task: `4514c4686aab4d0c89c5e24111d21a1f`
- Objective: Deliver the fully accepted PR #17 repair to origin/main. Preserve every repository-root .coding-tools artifact, include the tracked nested ledger removal plus its byte-identical relocation under .coding-tools/migrated, include the two repaired regression tests, run the repository delivery guard exactly around staging/commit/push, commit all intended current changes, and push main. Do not alter production runtime code, do not ignore or omit any .coding-tools evidence, and fail closed if origin/main has advanced from the current HEAD.
- Status: **accepted**
- Started: `2026-08-18T08:49:55.460Z`
- Finished: `2026-08-18T08:52:20.094Z`

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
| 1 | `34a6a03ef174481680a119ce745997da` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 2 | `edf51819b8d741d38696d543d92c4308` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 3 | `389c8ea8e3014491a62fe63db633e7a2` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 9c77dbfe67eb44b2a0004c604dcdebbb | 389c8ea8e3014491a62fe63db633e7a2 | accepted | f6018a5420c28b5da3e6effc456ee07da25a14ed | ba08e1f5680a9f035e36d25eb49bd0fd71237ab86cfc02c1577c53b2e35725d0 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16690 | `deterministic` | `deterministic` | explicit_request |
| 16714 | `deterministic` | `deterministic` | explicit_request |
| 16729 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16706 | `CHECK_FAILED` | `PROVING` |  |
| 16721 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `58`
- Chain head: `6a6e996b7350ff7c20d6ebc8c5931a5eb48780860ece55ec590a0a2fecca4d6a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
