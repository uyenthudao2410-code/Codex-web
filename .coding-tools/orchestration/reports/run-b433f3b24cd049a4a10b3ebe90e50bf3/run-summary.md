# Orchestration Run Summary

- Run: `b433f3b24cd049a4a10b3ebe90e50bf3`
- Task: `640be5c21589438697556060bfd65d10`
- Objective: Forensic-only execution for the accidental secondary orchestration ledger. Run bounded READ-ONLY SQLite comparison between canonical .coding-tools/orchestration/ledger.sqlite3 and resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3. Do not modify either database or any repository file. Report integrity_check, schema/table counts, DB size, run/wave/event/proof/checkpoint and P5 table counts where present, min/max timestamps/sequence where available, and set differences of durable primary identifiers (run_id, wave_id, event_id, proof_id, checkpoint_id, experiment_id/assignment_id where applicable). For any identifiers unique to the nested DB, return only bounded content-free provenance fields needed to classify them: ids, status, task_id, timestamps, provenance/type flags and workspace/source identity hashes if present; do not dump prompts, stdout/stderr, secrets, raw payloads, or large metadata. Determine whether the nested ledger contains unique real project evidence, duplicate rows, or only test/synthetic/empty schema evidence. Do not delete/migrate/archive/edit/commit/push/restart or alter P5 state.
- Status: **accepted**
- Started: `2026-08-22T13:52:02.726Z`
- Finished: `2026-08-22T13:54:20.823Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `4428515f7a1348c8bc4ec5bac75ff040` | 1 | `run_initial_objective` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 2 | `72a6785de167435892393e0d9215843b` | 2 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | replanned |
| 3 | `88a6b259099a40898792f7a97f012ead` | 3 | `replan_request` | `mcp_only` | `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| cb6920206568475f8c76073b7635c997 | 88a6b259099a40898792f7a97f012ead | accepted | 6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0 | 471951c4eaacbfc5371f1b9006b2ad6e189025e08375148854c1f76f7cf34107 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27151 | `deterministic` | `deterministic` | explicit_request |
| 27164 | `deterministic` | `deterministic` | explicit_request |
| 27177 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 27158 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 27168 | `INVALID_ARGUMENT` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `59aee1fe0789a7a2822109b3793c353ec84e7de10a0520299ba2f96ff6e60572`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
