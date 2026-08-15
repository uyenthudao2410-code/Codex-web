# Orchestration Run Summary

- Run: `28bd721b83b34d67a76c039988c6e32c`
- Task: `8565852a72f844748a066e998ef77b83`
- Objective: Fix paired_policy_evaluation measurement overhead without changing evaluation semantics. The real ledger scan over ~260 mostly-untagged runs exceeded 30 seconds because the evaluator materialized accepted_result_evaluation for every run before rejecting untagged history. Filter evaluation-tagged baseline/candidate rows in SQLite first, then materialize economics only for those rows. Preserve the bounded 500 tagged-row cap, report total ledger_run_count and tagged_runs_scanned truthfully, keep representative/source/oracle/quality/cost gates unchanged, and keep zero-pair behavior fail-closed. This is a localized measurement-performance bugfix only; do not change routing/review/provider behavior and do not call providers.
- Status: **accepted**
- Started: `2026-08-15T04:32:51.526Z`
- Finished: `2026-08-15T04:33:14.367Z`

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
| 1 | `24e47493cd204408bc9e83c692cc3683` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| bec22af4dbab41a0b6efed5bf16b5da5 | 24e47493cd204408bc9e83c692cc3683 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 151cd914a6da41d2a06b7b05eec17d8316563b97c70cac513b0fc9fba4487a40 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4223 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `37c63f026d08c6fa407f8f56792a369ff6bde966613734fdc28f80b8f5d2ac02`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
