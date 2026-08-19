# Orchestration Run Summary

- Run: `8206ecadd3884b5d956f30dd1d66bbbd`
- Task: `5e76eba8ee1846858c96ae94a6e6c683`
- Objective: Diagnose the single failing multi-root regression only. Do not modify source. Run the focused workspace/session isolation test verbosely so the exact assertion/error is captured before the correction wave continues.
- Status: **accepted**
- Started: `2026-08-19T05:04:54.102Z`
- Finished: `2026-08-19T05:05:11.974Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2fc401881df846248b289bf8e77f8806` | `mcp_only` | `7c1c93ea72fa3465d718f7826494629426c1a9e8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a2335fb64fc04928924c1be47645ed8b | 2fc401881df846248b289bf8e77f8806 | accepted | 7c1c93ea72fa3465d718f7826494629426c1a9e8 | adfcb4584e938d016a8e611003f2e6e112b7b1b10ff3b24f618a1576855fbbaf | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 19724 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 19733 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `c6c7542beaaccedf225ff274729c6a2a46fb176ab7aed436b1065d231aa454e5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
