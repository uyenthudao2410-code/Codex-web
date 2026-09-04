# Orchestration Run Summary

- Run: `94609e3a8e4748c49a2deaba12d3c840`
- Task: `b2f9a0d4aea7438cb4b058ecbbd3ff73`
- Objective: Fresh live L3 controller-usage canary after the successful UI/runtime activation. Bind this exact current ChatWeb turn to a new exact RUN/WAVE through the supported content-free host correlation path. Do not mutate source files, do not restart runtime, and do not read or persist prompt/assistant bodies. Preserve the canary long enough for post-response controller_usage to arrive; controller token fields must remain unknown_not_zero unless exact numeric usage is observed. This canary is for live evidence only and must be terminalized after post-response inspection.
- Status: **aborted**
- Started: `2026-09-03T16:07:35.702Z`
- Finished: `2026-09-03T16:12:15.336Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `26f6cfd4ad87426590fc31662a026131` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 2 | `c46383f33ad84f4785412a8911d51467` | 2 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 37694 | `deterministic` | `deterministic` | explicit_request |
| 37711 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 37700 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 37730 | `SOL_REJECTED` | `ACCEPTING` | Reject this read-only L3 canary as non-qualifying live evidence. The content-free journal shows the current user turn was already older than the 120s pending-host-turn TTL when the canary RUN/WAVE executed, both pending and binding files were missing, no host turn/trace was attached to this RUN/WAVE, and usage_event_count remained 0. Preserve controller usage as unknown_not_zero; do not accept or splice this canary into L4. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `292b154c4e93b0b544d848b69e6205158521b8963d81912c6207c692e78bd0a3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
