# Orchestration Run Summary

- Run: `714feb67173f45a4821b2e15aa887bc7`
- Task: `d3d3cf001f934f0682f509191cf31b65`
- Objective: Post-activation L3 live canary only. Create one fresh content-free ChatWeb-controlled diagnostic RUN under the current activated runtime and execute exactly npm run dev:status as the sole command/oracle. Do not modify source, do not clean/reset/revert, do not restart, commit, push, release, deploy, or invoke provider work. Preserve server-derived host correlation only; do not trust caller-supplied turn_id or trace_id. The purpose is to observe whether the activated attested_chatweb_transport_trace path binds this fresh ChatWeb turn and later receives exact controller usage. Missing usage must remain unknown_not_zero.
- Status: **accepted**
- Started: `2026-09-03T16:47:25.199Z`
- Finished: `2026-09-03T16:48:12.904Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d343dc4a80dd46c09fc8ad3546452ce5` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ee7321d9a6a944fea700f41b98da6ef3 | d343dc4a80dd46c09fc8ad3546452ce5 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | f2c79fb6129ed25aa26ad9e24affc0833474174c41dd7ac0f0d97658468a0430 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 38044 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `1da02f6b44d899a677ad1807b3ab3a86cde96c21c18554ce570cac68625dc420`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
