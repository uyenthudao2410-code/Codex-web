# Orchestration Run Summary

- Run: `88c37ce342e94f409db1d4c926ac0ca4`
- Task: `76fa499c08e8453a8d69fb461974b675`
- Objective: Unblock apples-to-apples accepted-run routing analysis with the smallest historical-compatible telemetry change. Extend the standalone runtime activation benchmark to schema v2 and derive durable accepted-run cohorts without any SQLite schema migration. Cohort dimensions: entry_surface, route, task_class, acceptance_status, repair_status. Derive entry_surface='agent_workflow' only when existing run metadata contains both workflow and phase; otherwise 'unknown'. Derive task_class from metadata.task_class or metadata.workflow, route from the latest durable route_selected event, and repair_status='repaired' when any wave for the run is replanned, otherwise 'first_pass'. Keep the existing global accepted_run_tta. Add accepted_run_cohort_coverage and a deterministic accepted_run_cohorts list with n/p50/p90. Never invent missing dimensions. Add focused tests for complete first-pass cohort, repaired/latest-route cohort, and unknown fallback. Do not modify database schema or runtime orchestration semantics.
- Status: **accepted**
- Started: `2026-08-14T02:26:47.567Z`
- Finished: `2026-08-14T02:27:07.806Z`

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
| 1 | `420d4d2c647a408284a453a227b325d1` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| afe88732ff0e44d0adff2ee5382a7b41 | 420d4d2c647a408284a453a227b325d1 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 297a31300fedd9d4e9a99772c1cef7c68ca7d646f5a36ea39229144e4abc04f2 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 703 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `e6a3806dfcc7349e61557e928acd6aab19a19f2192bcbdd57f250dae6f2ff553`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
