# Orchestration Run Summary

- Run: `0c7934363c5240c79c40371c9e0e29f0`
- Task: `2a978b6fdda04cd69f6671a582e81a8d`
- Objective: Validate accepted-run cohort telemetry v2 against the current durable production ledger. Run the canonical runtime activation benchmark after the accepted schema-v2 benchmark change. Capture cohort coverage and the homogeneous cohort breakdown. Do not compare raw global TTA across mixed workloads. Do not modify source files, commit, push, restart, or deploy.
- Status: **accepted**
- Started: `2026-08-14T02:27:19.549Z`
- Finished: `2026-08-14T02:27:51.348Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3cc1e2b5ab764b4e8d08fdb20e243997` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 83c39088c9ea4f5bbf0b3bb63011f652 | 3cc1e2b5ab764b4e8d08fdb20e243997 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 9152b6bbb84c561ba986d9b26f27ddee35fe59e631219d84ce0e2efb0a6f4226 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 717 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `231d4aa29e7e7254dc8af4540b09905fa7e01c48418e0f13987c56f0c619b975`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
