# Orchestration Run Summary

- Run: `1cd4db2e927b45afb1356bdb1cc43ba5`
- Task: `aa8a807b2c03403a98dcb10cc22710b4`
- Objective: P1 accepted-run production sample after the handoff shadow A/B. Run the repository's canonical runtime activation/production telemetry benchmark on the current checkout and capture the current accepted-run TTA sample plus activation/idempotency/proof-cache counters. Do not modify source files. Treat mixed workload averages cautiously: report whether the benchmark exposes enough cohort dimensions (entry surface, route, task class, accepted/repair status) for apples-to-apples comparison. If not, mark cohort calibration as still pending rather than comparing raw global averages. Do not commit, push, restart, or deploy.
- Status: **accepted**
- Started: `2026-08-14T02:23:20.499Z`
- Finished: `2026-08-14T02:23:58.123Z`

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
| 1 | `3917b24b7de2417f9111baeb779a8bc2` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 428fd4aac81e408ea7c7951fa463a2f4 | 3917b24b7de2417f9111baeb779a8bc2 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 38236db57c1ada9e8e1771e7a44c27d901bee006fdedb3c7ab54bbec3fc1d681 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 689 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `947906e8ee74dedd9705fa5153abb03d73faaa424e7996f435a2514cdbfd49a7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
