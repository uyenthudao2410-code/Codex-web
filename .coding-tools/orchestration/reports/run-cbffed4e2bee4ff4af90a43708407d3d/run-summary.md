# Orchestration Run Summary

- Run: `cbffed4e2bee4ff4af90a43708407d3d`
- Task: `bdd2998e87df43db87a1b68c8b216638`
- Objective: P0 remediation: reproduce and root-cause intermittent agent_workflow/TaskGroup ExceptionGroup collapse while workspace_context remains healthy. Identify the exact child exception path, make it typed and non-collapsing, add focused regression proof, and preserve the 8-tool public contract. Do not touch P1/P2 in this run.
- Status: **accepted**
- Started: `2026-08-17T19:11:41.566Z`
- Finished: `2026-08-17T19:18:11.867Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `adf0bbcb34844192adcaef633f655db8` | `mcp_only` | `775d92716f90ada3cfa909d8f0069c46d204ab51` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 00c2973847ec4c4887db6e29c7ef225e | adf0bbcb34844192adcaef633f655db8 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | ca61459c9155ed70c91e064b1a16d62fcfcf10e8d0fde113889ecc0179895796 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15497 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `33067a952384b3c7a718d9f7a642fd627aa22be735c1db067d474e1f71a4dcbd`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
