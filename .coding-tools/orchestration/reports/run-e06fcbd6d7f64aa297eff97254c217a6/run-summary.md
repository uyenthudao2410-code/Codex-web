# Orchestration Run Summary

- Run: `e06fcbd6d7f64aa297eff97254c217a6`
- Task: `0ad851bf297e46c8ba47db09f96d07d4`
- Objective: Find stale R1 observability test expectations after R2B dispatch was enabled. Search only for assertions or fixtures expecting compute.mode="shadow" or compute.dispatch_enabled=false, especially runtime_status tests. Return exact locations; do not modify files.
- Status: **accepted**
- Started: `2026-08-16T13:15:37.729Z`
- Finished: `2026-08-16T13:16:55.555Z`

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
| 1 | `268172e916ef4268aa4a85d39003a647` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ec65e00944904845ab9a98d9339af834 | 268172e916ef4268aa4a85d39003a647 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 7684760c1edea4ab90f4fb35aaadb1ccd5b05cea587e8ec200ee84a0ebdd7784 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8363 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `03e0dad361c6b89999fe1ca52435fb4e1799dadffb2084802eaddd62c6c2f653`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
