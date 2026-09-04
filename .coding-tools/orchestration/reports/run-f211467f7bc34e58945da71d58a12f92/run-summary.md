# Orchestration Run Summary

- Run: `f211467f7bc34e58945da71d58a12f92`
- Task: `c188d6ac52544bfb99aa3cbe07179250`
- Objective: G2-P2 provenance closure only for the exact current untracked usage reservation packet. Adopt, without changing source bytes, exactly resources/coding-tools-mcp/coding_tools_mcp/usage_reservations.py at SHA-256 8f0f9abfa28d623303bc15ea0412054f6421b9f62f9edddeec5d9f87c4734f1e and resources/coding-tools-mcp/tests/test_usage_reservations.py at SHA-256 02dd380ecb49f021eea7065eb0d07e1124ca53140b2a2b2ecb854db62744dc74. Prove the reservation lifecycle is durable on the canonical event ledger: estimates never become actual usage; absent exact usage remains indeterminate/unobserved rather than zero; reserve/reconcile are idempotent; conflicting or expired authority fails closed; late exact reconciliation is valid; abort is terminal for dispatch. provider_runtime.py, server.py, and test_execution_hub.py are ACCEPTED_CURRENT context only and must not be adopted or modified. Preserve all concurrent WIP and all paths outside this two-file scope. No bulk adoption, direct SQLite access/mutation, fake outcome/cohort data, process/lease manipulation, reconcile of stale runs, restart, reset, restore, clean, rebase, commit, push, tag, release, publish, or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Status: **accepted**
- Started: `2026-09-03T16:31:11.012Z`
- Finished: `2026-09-03T16:32:26.865Z`

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
| 1 | `efe5370263c644a28266a1a8fec93e30` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 5264626e664149179121ae4bef212e24 | efe5370263c644a28266a1a8fec93e30 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 69dc3c268264575427f85116f5376f8694153f01832bd3d8f3193d1f819581db | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 37884 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `a32a99624da29da9b74f754aa4bc04a546554ff5c2f2204531849b90f7412cb8`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
