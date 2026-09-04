# Orchestration Wave 1

- Run: `47fe870795d1499cb7d1e0782593192c`
- Wave: `a8af6d54526b4363a465986616860b85`
- Objective: Implement the prepared exact-RUN archived-projection recovery repair only. The canonical orchestration ledger remains authority. Extend stateless exact-run lookup so a registered context may be recovered from bounded TaskState history when the archived row matches both requested run_id and the canonical ledger task_id, while retaining the existing exact current-projection path and controller-owner check. Fail closed if more than one context matches, the current scoped task has a pending completion report, the current conflicting task/run is nonterminal or active, history identity is missing/mismatched, workspace binding is invalid, or current ChatWeb controller ownership mismatches. Extend projection reconciliation with an explicit requested_run_id path: only after the same archived exact identity and safe-replacement checks, archive/clear the terminal polluted compact task projection using TaskStateStore APIs and restore the canonical task_id/objective plus current orchestration projection from the exact ledger; never modify the orchestration ledger. Pass requested_run_id from task_control into reconciliation before dispatch. Keep default reconciliation behavior unchanged when no exact run is requested. Add regression tests reproducing the real failure: canonical context/run archived/replaced by a failed auto-start-like task, then task_control get/audit with run_id and no task_context recovers the original context and canonical task; also prove active conflicting current task and pending operator report refuse history recovery. Preserve 8-tool contract, workspace isolation, unrelated dirty bytes and all token/accounting code. No W4 source, no restart, commit, push, release or deploy.
- Objective revision: `1`
- Objective SHA-256: `ee64c325d3c7d8297112d9b8a958cbdc8bb9cf6f5f9c2a08755752d2c1f1ad12`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `cd9fdac8b4ee50cfe307293d1356ef0f974776cd285d00e4dd4355cdb040bbad`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34075 | 2026-09-01T01:51:04.042Z | run_started |  | PREFLIGHT |  |
| 34076 | 2026-09-01T01:51:04.411Z | observation_span_recorded |  |  |  |
| 34077 | 2026-09-01T01:51:28.207Z | solution_shadow_recommended |  |  |  |
| 38784 | 2026-09-03T19:42:52.845Z | state_transition | PREFLIGHT | ABORTED | reason=G3_RECONCILE_COMPLETED_BUT_STALE_PROJECTION |
| 38785 | 2026-09-03T19:42:53.302Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `5`
- Chain head: `c893acfa347cec7ac0043dbfbc77f7391dfe9d8adb9cbfb52464222f070d00f5`
