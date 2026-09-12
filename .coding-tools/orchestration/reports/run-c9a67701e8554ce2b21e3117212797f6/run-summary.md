# Orchestration Run Summary

- Run: `c9a67701e8554ce2b21e3117212797f6`
- Task: `a0983269792947b9b0355d9e916e9634`
- Objective: Diagnose N21 maintenance path causally before any further restart. Explain from current source/runtime why a controlled restart with exact_stale_runs containing more than two eligible zero-ownership RUN IDs only reconciles two, and why an accepted controlled restart can drop the Coding-VP Live tunnel without automatic connector return. Identify the smallest coherent source fix that allows one bounded exact maintenance request to reconcile all explicitly eligible zero-ownership stale RUNs safely, leaves below-threshold/live-owned RUNs untouched, and restores/reattaches the connector automatically after handoff. Preserve all unrelated dirty bytes. Do not mutate, restart, reset, clean, commit, push, package, release, or deploy in this prepare step.
- Status: **active**
- Started: `2026-09-11T03:09:24.832Z`
- Finished: `None`

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
| 1 | `19db767439c4435a843cc7ecbdbe57df` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | active |

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
- Events checked: `61`
- Chain head: `6a692f3ea8000211f93eaced2342a668de543948ab993ce363b1593b6e88adaf`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
