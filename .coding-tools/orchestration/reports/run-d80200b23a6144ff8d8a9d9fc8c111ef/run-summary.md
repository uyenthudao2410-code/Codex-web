# Orchestration Run Summary

- Run: `d80200b23a6144ff8d8a9d9fc8c111ef`
- Task: `e8c1aaaca8114927b748bef51989bffb`
- Objective: G2-P6 provenance closure only for the exact durable Full Clean epoch-monitor packet. Adopt without changing source bytes exactly electron/services/recoveryActionStore.js at SHA-256 6b9ddd28aa29ca81ad6c5a3b2586847762839d7aabf076837b7ba392aaab62e5, electron/services/recoveryActivation.js at SHA-256 b0696cf3eae0523e04d2b1ae2a4095c0314d4e7f22eb46932ebaa8ed19f2274a, and tests/recovery-activation.test.js at SHA-256 e07a9c22ae26eaeb401c13f8139fb5070fb1e888f8de9169c6863ac28e8085a0. Prove the sole causal objective: separate the short request-admission TTL from the bounded durable Full Clean epoch-monitor lifetime; bind the durable invariant to exact operation_id + activation_epoch_id + expiry; validate it on reload; reject malformed, mismatched, conflicting, over-bound, or tampered evidence; and use the durable deadline only after the exact accepted action has been bound. Preserve request expiry as audit data. Replay must reattach the same epoch and must not create a second transaction. Preserve all concurrent WIP and every path outside this exact three-file scope. Do not run live restart, activation, process kill, process adoption, bulk adoption, direct SQLite, force-release, stale-run reconciliation, reset, restore, clean, rebase, commit, push, tag, release, publish, or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Status: **accepted**
- Started: `2026-09-03T16:57:30.075Z`
- Finished: `2026-09-03T16:58:44.628Z`

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
| 1 | `44da2aa89ae840b18932f7c420559954` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 1299c60deec2490c8950f4d72857353f | 44da2aa89ae840b18932f7c420559954 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 58ad77a5338a55a51571b00b149a37bd8b84d80479a4b341938e510ec6e3724e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 38220 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `30afe4ac1835769d6e2eb6ae906be452c3ab6bf7e8785b9d125ad79403d9a574`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
