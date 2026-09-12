# Orchestration Run Summary

- Run: `742eff5143bf45e6aa42febdd4e14018`
- Task: `9f43bd1fcfbc44edb20f4fbb7c0f69bb`
- Objective: Converge Recovery Host and Coding MCP component state by no-patch provenance adoption of the exact current bytes for the 26 unaccepted component files, with fresh deterministic proof and no source writes.
- Status: **aborted**
- Started: `2026-09-08T17:36:37.211Z`
- Finished: `2026-09-09T10:48:21.619Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f99d36d4509b4402b0dc6e43adaf2ceb` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `8c4c360ed7bb4e109cd438d52909efb5` | 1 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 44148 | `deterministic` | `deterministic` | explicit_request |
| 44162 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 44154 | `EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED` | `EXECUTING` |  |
| 44182 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `2979843ece71fbb63c7b0a818f2d0652aba5779575f33465b44d48759129569b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
