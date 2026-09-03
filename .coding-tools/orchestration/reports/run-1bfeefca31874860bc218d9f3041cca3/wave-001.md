# Orchestration Wave 1

- Run: `1bfeefca31874860bc218d9f3041cca3`
- Wave: `58c03cee6b8f4caba196e83f14b2c7ce`
- Objective: Repair the stateless exact-RUN recovery control-plane defect blocking Token W4. Canonical orchestration ledger remains authority. Exact task_control continuation with requested run_id and no task_context_id must recover the original registered task context even if its canonical task projection was archived/replaced by an auto-start-like or other terminal polluted compact task projection, but only when archived history matches both requested run_id and canonical ledger task_id, the current conflicting projection is safely terminal and has no pending operator completion report, workspace binding matches, and current ChatWeb controller ownership matches. Multiple matching contexts, active/nonterminal conflicting task or run, pending report, missing/mismatched history identity, foreign controller, or workspace mismatch must fail closed. Reconciliation must accept requested_run_id, archive/clear only the safe compact TaskState projection via official TaskStateStore APIs, restore canonical task identity/objective and orchestration projection from the exact ledger, and never mutate orchestration ledger history. task_control must pass requested_run_id into reconciliation before dispatch. Keep default reconciliation unchanged when no exact run is requested. Add discriminating tests for: archived canonical projection replaced by failed auto-start-like task recovers original context and canonical task with no caller task_context; active conflicting task refuses; pending operator report refuses; existing foreign-controller refusal remains valid. Preserve exact smart-v3 8-tool contract, all token/accounting semantics, and unrelated dirty bytes. No W4 implementation in this run; no restart, commit, push, release or deploy.
- Objective revision: `1`
- Objective SHA-256: `f15e3a15871ee43720ec097f8739784979b4128705f5b79295ebc2a78b38e83c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `cd9fdac8b4ee50cfe307293d1356ef0f974776cd285d00e4dd4355cdb040bbad`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34080 | 2026-09-01T01:52:06.177Z | run_started |  | PREFLIGHT |  |
| 34081 | 2026-09-01T01:52:06.723Z | observation_span_recorded |  |  |  |
| 34082 | 2026-09-01T01:52:06.941Z | solution_shadow_recommended |  |  |  |
| 34083 | 2026-09-01T01:52:07.838Z | observation_span_recorded |  |  |  |
| 34084 | 2026-09-01T01:52:08.074Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 34085 | 2026-09-01T01:52:08.469Z | managed_process_admitted |  |  | owner=default |
| 34086 | 2026-09-01T01:52:08.899Z | managed_process_started |  |  | owner=default |
| 34087 | 2026-09-01T01:52:09.373Z | managed_process_terminal |  |  | owner=default |
| 34088 | 2026-09-01T01:52:09.586Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 34089 | 2026-09-01T01:52:09.791Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34090 | 2026-09-01T01:52:09.977Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34091 | 2026-09-01T01:52:10.160Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 34092 | 2026-09-01T01:52:10.368Z | state_transition | READY | ROUTED | reason=route_selected |
| 34093 | 2026-09-01T01:52:10.589Z | observation_span_recorded |  |  |  |
| 34094 | 2026-09-01T01:52:11.368Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b7470855ad794cc98aaac78290ff6f0f |
| 34095 | 2026-09-01T01:52:11.583Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34096 | 2026-09-01T01:52:12.246Z | observation_span_recorded |  |  |  |
| 34097 | 2026-09-01T01:52:12.650Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b7470855ad794cc98aaac78290ff6f0f |
| 34098 | 2026-09-01T01:52:12.858Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34099 | 2026-09-01T01:52:13.660Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cfce9bd5a942c554; input_fingerprint=044a45696db4198caf2da231a798d3927fea7e42b4437a863585b9721d6ae20e |
| 34100 | 2026-09-01T01:52:14.085Z | managed_process_admitted |  |  | owner=default |
| 34101 | 2026-09-01T01:52:14.483Z | managed_process_started |  |  | owner=default |
| 34102 | 2026-09-01T01:52:14.919Z | managed_process_terminal |  |  | owner=default |
| 34103 | 2026-09-01T01:52:15.313Z | proof_recorded |  |  | stage_id=check:cfce9bd5a942c554; status=failed; cache_hit=False; input_fingerprint=044a45696db4198caf2da231a798d3927fea7e42b4437a863585b9721d6ae20e |
| 34104 | 2026-09-01T01:52:15.515Z | observation_span_recorded |  |  |  |
| 34105 | 2026-09-01T01:52:15.941Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 34106 | 2026-09-01T01:52:16.143Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 34107 | 2026-09-01T01:52:16.353Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:cfce9bd5a942c554 | failed | 044a45696db4198caf2da231a798d3927fea7e42b4437a863585b9721d6ae20e | False | 1292 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `45404375dadcd7d7b5171d52eec0c8c67c79027a92d0128082ff23bf96e0fb9d`
