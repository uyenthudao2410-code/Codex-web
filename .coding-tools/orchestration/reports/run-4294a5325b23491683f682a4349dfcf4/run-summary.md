# Orchestration Run Summary

- Run: `4294a5325b23491683f682a4349dfcf4`
- Task: `14af6057b2ba4c30939cbf3493c049de`
- Objective: Run the remaining P1.1 exact-fingerprint RC source/security gates on the same accepted source baseline: Recovery host-process E2E, OpenCode Flash preflight only with no provider dispatch/cost, and production dependency audit. No mutations, no packaging yet, no commit/push/restart/deploy/release/tag/publish, preserve resident codex-app-server and all .coding-tools evidence.
- Status: **accepted**
- Started: `2026-08-21T04:17:19.956Z`
- Finished: `2026-08-21T04:25:23.507Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `59d86ab9def642ef868480162a322472` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | replanned |
| 2 | `77bade90a0f14742a9f03dcb22c174c5` | `mcp_only` | `640ad37e3e571a0a56af376e9d3bda2b89bf0669` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4985a252f36e424884da7732590253b9 | 77bade90a0f14742a9f03dcb22c174c5 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 80dc849961f359274da04319623df6213f39408f34aca09b9647ad48b8f3d607 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 25825 | `deterministic` | `deterministic` | explicit_request |
| 25849 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 25841 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `b938c363455bac996ccd8a921671a30162b8ca6c241f88704ce4c77145388b9b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
