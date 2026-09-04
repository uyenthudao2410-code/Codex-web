# Orchestration Wave 1

- Run: `56da798b0f47436f9af3fdc487c1bcba`
- Wave: `46484a0aa51e4ac18f0fcac5406cc553`
- Objective: Implement the exact-RUN archived-projection recovery repair in this current RUN/WAVE only. Canonical orchestration ledger remains authority. Extend stateless exact-run lookup to recover a registered task context from bounded TaskState history only when the archived row matches both requested run_id and canonical ledger task_id, preserving current-projection exact match and controller-owner checks. Fail closed for multiple matches, current pending completion report, active/nonterminal conflicting task or run, history/task identity mismatch, workspace mismatch, or foreign controller ownership. Extend projection reconciliation with requested_run_id so a safely replaceable terminal polluted compact projection can be archived/cleared through TaskStateStore APIs and restored from exact canonical ledger task identity without mutating the orchestration ledger. Pass requested_run_id from task_control into reconciliation. Keep default behavior unchanged without requested run. Add regression tests reproducing archived canonical projection replaced by failed auto-start-like task and exact run recovery with no task_context; prove active conflicting task and pending report refuse recovery. Preserve 8-tool contract, token/accounting code, unrelated dirty bytes. No W4 implementation, restart, commit, push, release or deploy.
- Objective revision: `1`
- Objective SHA-256: `1c3f1847525642b6f6bfd1376268e69cbf90ab9cb2b6d9d93aa02032153df49c`
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
| 34078 | 2026-09-01T01:51:41.381Z | run_started |  | PREFLIGHT |  |
| 34079 | 2026-09-01T01:51:41.763Z | observation_span_recorded |  |  |  |
| 38786 | 2026-09-03T19:45:36.589Z | state_transition | PREFLIGHT | ABORTED | reason=G3_RECONCILE_COMPLETED_BUT_STALE_PROJECTION |
| 38787 | 2026-09-03T19:45:37.142Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `4`
- Chain head: `02d925d18dab35e906edf8cd735c678784c3b8f38f80381451a24f8418dca768`
