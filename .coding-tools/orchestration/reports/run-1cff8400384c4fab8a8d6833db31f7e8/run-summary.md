# Orchestration Run Summary

- Run: `1cff8400384c4fab8a8d6833db31f7e8`
- Task: `561fe080749a4d7daff4c2ffa7f3537c`
- Objective: Make organic post-fix measurement observable without creating a run: when agent_workflow terminates on a known no-write patch-preflight failure, persist a content-free workflow_patch_preflight boolean in the durable idempotency summary alongside error_code/outcome_unknown. This lets later baseline analysis count avoided orchestration replans without synthetic workload. Add focused assertion only. No routing/provider/reviewer/restart changes.
- Status: **accepted**
- Started: `2026-08-15T05:35:24.116Z`
- Finished: `2026-08-15T05:36:29.819Z`

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
| 1 | `4f9b0b3dddd94db89d050ee3533ff897` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e677a10c823f4e35a15630bfdb520ef7 | 4f9b0b3dddd94db89d050ee3533ff897 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 1ad0b232328f915169853e065c51a726fed2965a623e7fa707bc364a0b5391aa | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4472 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `6bc070af3bf23e7d8bd25a98678f78f6a413a6b729364a021cdb869df555f99a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
