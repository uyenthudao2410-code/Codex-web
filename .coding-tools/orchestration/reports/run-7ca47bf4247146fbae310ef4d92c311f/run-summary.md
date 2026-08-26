# Orchestration Run Summary

- Run: `7ca47bf4247146fbae310ef4d92c311f`
- Task: `a9cbea22dc654b0fb7ce0119262f2015`
- Objective: Implement the smallest fail-closed acceptance fix: allow cached clients to transport acceptance_files only as payload.acceptance_files for action=accept, reject ambiguous/extra payload fields, and allow explicitly SHA-attested pre-existing dirty files only when they are inside the write lease and durable patch_surface_observed. Preserve ordinary acceptance exclusion of pre-existing dirty files and all protected/reparse/path guards. Update focused tests only.
- Status: **active**
- Started: `2026-08-26T04:32:30.129Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `4a5d5e767d8243d38afccde2d03df300` | 1 | `run_initial_objective` | `mcp_only` | `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 29990 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `9`
- Chain head: `a7e0c405c8ded0ac9497823da3d30d5859d09c2ea43d9d7c407341114d632bb6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
