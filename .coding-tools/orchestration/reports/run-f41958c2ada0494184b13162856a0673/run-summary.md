# Orchestration Run Summary

- Run: `f41958c2ada0494184b13162856a0673`
- Task: `e5dc52b18f004f929f8f4ab9ddc04aa0`
- Objective: Fresh live L3 controller-usage canary for the current ChatWeb turn. Immediately bind this exact current user-visible host turn to this new RUN/WAVE through the supported content-free electron_pending_host_turn correlation path. Do not mutate source files, restart runtime, or read/persist prompt or assistant bodies. Run only the read-only oracle `npm run dev:status`. Preserve controller token fields as unknown_not_zero unless exact numeric usage is observed. This canary is for live evidence only and must be terminalized after post-response inspection.
- Status: **aborted**
- Started: `2026-09-03T16:14:35.908Z`
- Finished: `2026-09-03T16:16:59.980Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `645fd19f9529410cba8645d118487142` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 37742 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 37767 | `SOL_REJECTED` | `ACCEPTING` | Reject this fresh scheduled-turn L3 canary as non-qualifying. The scheduled automation turn is not emitted into the integrated Electron ChatGPT DOM observer: both chatweb-host-turn-pending.json and chatweb-host-turn-binding.json are missing, the host observation journal has no record matching this RUN/WAVE, and its latest user_turn_visible is 2026-09-03T15:50:17.164Z, about 24 minutes before this RUN started at 16:14:35Z. Therefore the scheduler transport cannot supply the required <=120s electron_pending_host_turn receipt. Preserve controller usage as unknown_not_zero and do not splice this canary into L4. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `698f7faa16022ccb53bec83bc1086dce60fa850a25a4e093ced9d5f125c5fe68`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
