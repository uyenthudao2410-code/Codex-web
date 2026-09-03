# Orchestration Run Summary

- Run: `1bfeefca31874860bc218d9f3041cca3`
- Task: `751e6e5fa95844bea4fdd3700bc17eea`
- Objective: Repair the stateless exact-RUN recovery control-plane defect blocking Token W4. Canonical orchestration ledger remains authority. Exact task_control continuation with requested run_id and no task_context_id must recover the original registered task context even if its canonical task projection was archived/replaced by an auto-start-like or other terminal polluted compact task projection, but only when archived history matches both requested run_id and canonical ledger task_id, the current conflicting projection is safely terminal and has no pending operator completion report, workspace binding matches, and current ChatWeb controller ownership matches. Multiple matching contexts, active/nonterminal conflicting task or run, pending report, missing/mismatched history identity, foreign controller, or workspace mismatch must fail closed. Reconciliation must accept requested_run_id, archive/clear only the safe compact TaskState projection via official TaskStateStore APIs, restore canonical task identity/objective and orchestration projection from the exact ledger, and never mutate orchestration ledger history. task_control must pass requested_run_id into reconciliation before dispatch. Keep default reconciliation unchanged when no exact run is requested. Add discriminating tests for: archived canonical projection replaced by failed auto-start-like task recovers original context and canonical task with no caller task_context; active conflicting task refuses; pending operator report refuses; existing foreign-controller refusal remains valid. Preserve exact smart-v3 8-tool contract, all token/accounting semantics, and unrelated dirty bytes. No W4 implementation in this run; no restart, commit, push, release or deploy.
- Status: **accepted**
- Started: `2026-09-01T01:52:05.797Z`
- Finished: `2026-09-01T02:27:05.838Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `58c03cee6b8f4caba196e83f14b2c7ce` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `493ed8d7fbfb454d9351328b06350d08` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 44ce31aa6f5e463bbac4da347289f4c7 | 493ed8d7fbfb454d9351328b06350d08 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 3664beb6afc65ecfd0ae227b85564055e8a68e9c5d621e107eca9f64ed500251 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 34091 | `deterministic` | `deterministic` | explicit_request |
| 34133 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 34105 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `45404375dadcd7d7b5171d52eec0c8c67c79027a92d0128082ff23bf96e0fb9d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
