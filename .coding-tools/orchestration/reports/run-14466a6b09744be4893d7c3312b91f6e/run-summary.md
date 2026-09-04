# Orchestration Run Summary

- Run: `14466a6b09744be4893d7c3312b91f6e`
- Task: `331c9fac9c864b7bb5c7d975cb212cd0`
- Objective: Live post-activation L3 transport-correlation canary on the current external ChatWeb turn. Do not mutate source, restart runtime, or inspect/persist message bodies. Create only a fresh RUN/WAVE under this new task context, allowing the runtime to derive server-owned host correlation from the current attested ChatWeb transport trace when no Electron pending turn exists. Preserve controller usage as unknown_not_zero unless an exact numeric client-reported receipt is actually observed. This canary is read-only and will be terminalized after inspecting correlation/usage evidence.
- Status: **aborted**
- Started: `2026-09-03T16:48:39.463Z`
- Finished: `2026-09-03T16:49:33.975Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `b54a40f42d80466e8c7960f3b6ef1f2e` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `6`
- Chain head: `8295ba6991b9e96bfdaa156248fc28df1af29b55b7fa17ca6f84cb94c91baeea`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
