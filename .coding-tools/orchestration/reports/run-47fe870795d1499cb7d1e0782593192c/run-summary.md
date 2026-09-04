# Orchestration Run Summary

- Run: `47fe870795d1499cb7d1e0782593192c`
- Task: `f442ec932ac34e20b67e03240b6599ca`
- Objective: Implement the prepared exact-RUN archived-projection recovery repair only. The canonical orchestration ledger remains authority. Extend stateless exact-run lookup so a registered context may be recovered from bounded TaskState history when the archived row matches both requested run_id and the canonical ledger task_id, while retaining the existing exact current-projection path and controller-owner check. Fail closed if more than one context matches, the current scoped task has a pending completion report, the current conflicting task/run is nonterminal or active, history identity is missing/mismatched, workspace binding is invalid, or current ChatWeb controller ownership mismatches. Extend projection reconciliation with an explicit requested_run_id path: only after the same archived exact identity and safe-replacement checks, archive/clear the terminal polluted compact task projection using TaskStateStore APIs and restore the canonical task_id/objective plus current orchestration projection from the exact ledger; never modify the orchestration ledger. Pass requested_run_id from task_control into reconciliation before dispatch. Keep default reconciliation behavior unchanged when no exact run is requested. Add regression tests reproducing the real failure: canonical context/run archived/replaced by a failed auto-start-like task, then task_control get/audit with run_id and no task_context recovers the original context and canonical task; also prove active conflicting current task and pending operator report refuse history recovery. Preserve 8-tool contract, workspace isolation, unrelated dirty bytes and all token/accounting code. No W4 source, no restart, commit, push, release or deploy.
- Status: **aborted**
- Started: `2026-09-01T01:51:03.710Z`
- Finished: `2026-09-03T19:42:53.168Z`

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
| 1 | `a8af6d54526b4363a465986616860b85` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

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
- Events checked: `5`
- Chain head: `c893acfa347cec7ac0043dbfbc77f7391dfe9d8adb9cbfb52464222f070d00f5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
