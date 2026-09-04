# Orchestration Run Summary

- Run: `801d8e34171249fda53ec2851f0ab1b6`
- Task: `e482e40913264b608bd9094919f5d7b0`
- Objective: G2-P1 provenance closure only for the exact existing CANARY_TOKEN_BUDGET=4096 packet. Adopt, without changing source bytes, exactly scripts/execution-hub-provider-canary.js at SHA-256 a0c7e61c0b9a5dccff7b969cbdbf7320c39b5282889adac7c4a5aa0804eeb022 and tests/execution-hub-provider-canary.test.js at SHA-256 f4a4fbc8351b1e5b7d02becb00e4e380a2705547d918cd06d7d3fe22d9d33812. The source behavior is that the canary request carries token_budget=CANARY_TOKEN_BUDGET where CANARY_TOKEN_BUDGET=4096, and the focused test asserts dispatchedBody.token_budget equals that exported constant. Preserve all concurrent WIP and all paths outside this two-file scope. Do not run a live provider canary. No source write, bulk adoption, SQLite access, process/lease manipulation, reconcile, restart, reset, restore, clean, rebase, commit, push, tag, release, publish or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Status: **accepted**
- Started: `2026-09-03T16:25:56.563Z`
- Finished: `2026-09-03T16:27:16.632Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `21dc409278b1423582356dc17603b7c7` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f6a759abc6944d9d9f1822645dbe3a73 | 21dc409278b1423582356dc17603b7c7 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | c3f639adeb54f5e07ebd0c6f4d189938d6f32015a04cba75888b623916ba6d68 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 37827 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `683d76e27424cb49e9fd4b2e7f988c522c308556742b859849a9f01a66c44dcc`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
