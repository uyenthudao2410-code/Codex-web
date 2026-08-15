# Orchestration Run Summary

- Run: `9e876e4be1474898b882f6b1560bc35b`
- Task: `82316b1148cb4472860989995b095c6e`
- Objective: P1.C executor proof: add a focused integration test using a temporary local git repository to exercise explicit controlled replay execution. The test must create two counterbalanced pairs (four trials), verify every trial starts at the exact clean base HEAD, executes caller-supplied argv, records hashes/timing without inferring acceptance, and cleans temporary worktrees. This is software verification only and must not be treated as benchmark/ROI evidence.
- Status: **accepted**
- Started: `2026-08-15T08:14:20.124Z`
- Finished: `2026-08-15T08:14:41.698Z`

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
| 1 | `626716c8eaba49c68f134a4ae213dd97` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f887b4b61ae34cb7b15f40fd07ea8df3 | 626716c8eaba49c68f134a4ae213dd97 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 3a334f033d1dc8721ce3798cd31864ac9081b5435e9a76b5591ec8a900cd3e0f | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4957 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `4b87110e640f1b2661d8402bcff8a8060607c495eeec3204f22896c8bea016e2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
