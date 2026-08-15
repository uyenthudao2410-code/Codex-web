# Orchestration Run Summary

- Run: `c8bc935c8d9e4b9180c99a12e841d7fa`
- Task: `a7d4f9e6bcf347a0a4454603d64fb70e`
- Objective: Live post-restart baseline-policy probe only. Confirm that execution_route=auto resolves deterministically under the ROI measurement hold and collect no provider candidate. Do not modify files, do not run external review, and do not treat this diagnostic probe as representative evaluation evidence.
- Status: **accepted**
- Started: `2026-08-15T04:43:41.113Z`
- Finished: `2026-08-15T04:44:40.610Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `288ed6e060e747809e178135f279eec0` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `0128066798a64eb5bf303927927776a1` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b12ae6d5acbd41e38a9dfa0e8158f5ad | 0128066798a64eb5bf303927927776a1 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 7c838cdeecf99c049e70227af3ca73ce074e68e88c74d6241a83a2fb6913a6df | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4250 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |
| 4261 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4254 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `1bf2e99881be9f86cfd57353476e5674fa92fafdf7cd65e295125352bb5a8bc1`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
