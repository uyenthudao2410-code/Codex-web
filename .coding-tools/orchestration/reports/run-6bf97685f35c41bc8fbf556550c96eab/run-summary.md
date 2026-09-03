# Orchestration Run Summary

- Run: `6bf97685f35c41bc8fbf556550c96eab`
- Task: `9ab14a639d7c471998f36c2a61c844a5`
- Objective: Repair the accepted-code Full Clean lifetime boundary so a valid short-lived authenticated activation request (max 60s) can create and monitor the separate durable Full Clean epoch (designed for 10 minutes) without RecoveryActionStore terminalizing the linked action at the original request deadline. Preserve normalizeActivationRequest/MAX_REQUEST_TTL_MS=60000 and immutable original request expiry; after FullCleanActivation returns the exact operation-bound durable epoch, bind the linked action to a separately named bounded durable epoch expiry only after exact operation/epoch identity validation; replay/get/active and accepted-code monitoring may use that expiry only for a valid exact durable epoch binding, otherwise retain request-expiry behavior; terminal/failed epochs remain fail-closed. Modify only electron/services/recoveryActivation.js, electron/services/recoveryActionStore.js, tests/recovery-activation.test.js. Do not touch concurrent WIP in fullCleanActivation.js, recoveryHost.js, full-clean-activation.test.js, recovery-host.test.js. Reach ACCEPTING after focused proof; do not self-accept.
- Status: **accepted**
- Started: `2026-09-02T09:52:26.289Z`
- Finished: `2026-09-02T10:06:22.264Z`

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
| 1 | `07265af168e04b3eb452bb9e21350b7e` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c213617ecc4941ac907433e69bc64e6c | 07265af168e04b3eb452bb9e21350b7e | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | b2c51aa749f2e70c31a3a6d37dda91794875842f7602cec979524d8f1a6a7bb3 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35765 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `c806532929fa3f6fb4ca4cd0670f6be6aa08962a54a928a12973d203c729f6c2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
