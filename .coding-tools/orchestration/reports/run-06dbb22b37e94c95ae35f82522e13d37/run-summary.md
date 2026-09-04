# Orchestration Run Summary

- Run: `06dbb22b37e94c95ae35f82522e13d37`
- Task: `58bb69bfaf0a4c5ca1a9ebd4fd05b80d`
- Objective: Repair the accepted-code Full Clean lifetime boundary so a valid short-lived authenticated activation request (max 60s) can create and monitor the separate durable Full Clean epoch (designed for 10 minutes) without RecoveryActionStore terminalizing the linked action at the original request deadline. Preserve normalizeActivationRequest/MAX_REQUEST_TTL_MS=60000 and immutable original request expiry; after FullCleanActivation returns the exact operation-bound durable epoch, bind the linked action to a separately named bounded durable epoch expiry only after exact operation/epoch identity validation; replay/get/active may use that expiry only for a valid exact durable epoch binding, otherwise retain request-expiry behavior; terminal/failed epochs remain fail-closed. Modify only electron/services/recoveryActivation.js, electron/services/recoveryActionStore.js, tests/recovery-activation.test.js. Do not touch concurrent WIP in fullCleanActivation.js, recoveryHost.js, full-clean-activation.test.js, recovery-host.test.js. Reach ACCEPTING after focused proof; do not self-accept.
- Status: **aborted**
- Started: `2026-09-02T09:48:04.846Z`
- Finished: `2026-09-03T19:53:49.211Z`

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
| 1 | `57fd3cb3525642bbb0cf1553b51732e9` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

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
- Events checked: `18`
- Chain head: `50d9819bfd944d27178ef6d3a22b7187682ff0bff9e0005d4e062dfa0d282cc3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
