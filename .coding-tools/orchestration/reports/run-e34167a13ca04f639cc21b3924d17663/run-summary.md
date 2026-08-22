# Orchestration Run Summary

- Run: `e34167a13ca04f639cc21b3924d17663`
- Task: `49db2849f3d64d8c80b641b7a47aeea8`
- Objective: Remove only the verified zero-data accidental nested state directory resources/coding-tools-mcp/.coding-tools, then prove the accepted reporter fix prevents recurrence from component CWD. Preconditions are already established: nested ledger integrity=ok, all durable/P5 counts=0, and source fix is CHECKPOINTED. Preserve canonical root .coding-tools history exactly. Do not edit source. In component workdir: delete only .coding-tools; run implicit-default P5 baseline, P2 diagnosis, and orchestration-tax; fail if .coding-tools reappears; run git diff --check. No commit/push/restart/P5 activation.
- Status: **accepted**
- Started: `2026-08-22T14:08:51.398Z`
- Finished: `2026-08-22T14:10:29.179Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `df7cd4f102a14aa0a2f5ab08b3c4903c` | 1 | `run_initial_objective` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 2 | `32b1faece0f54952a24a676d6ebb3793` | 2 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6d321dbd77a94e44a3ee90c80ec22c88 | 32b1faece0f54952a24a676d6ebb3793 | accepted | 6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0 | 286c43f99fca42535ca19bbb6c22b53c94a9e5e94fb177efab4dcf43c6ed9b51 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27288 | `deterministic` | `deterministic` | explicit_request |
| 27306 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27300 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `58`
- Chain head: `23b7ab0d9cd71b20ba2c3014276d6a6edec6b5e914f261a6083fdb39c27c4075`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
