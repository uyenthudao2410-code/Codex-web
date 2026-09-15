# Orchestration Run Summary

- Run: `5fa9565664c8496ba69f64585383a54c`
- Task: `0dbffa7b669f487cbbbd4400154302fb`
- Objective: Read-only diagnose why the explicitly accepted controlled restart ticket restart-vUipuqfM0aIdvu1o was not consumed before expiry: process_instance_id aiH9Kyigz45aDihj and server_instance_id dEld38_Om9Zrj_AZ remained unchanged after the ticket window. Inspect only the narrow restart-ticket producer/consumer, Electron supervisor polling/consumption path, expiry/admission semantics, and any durable evidence for this exact ticket. Determine the smallest safe next action. Do not restart, mutate source, accept/reject C01, stop active non-stale work, reset/clean, commit, push, package, release, or deploy.
- Status: **aborted**
- Started: `2026-09-15T09:05:20.683Z`
- Finished: `2026-09-15T09:17:06.354Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `40d4c5bdc65e40a1be38ca335d06262e` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `c94099cf894ee18fd9d58dc2c51b3eb6147deffac060efd10b4ab01fd98d5c87`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
