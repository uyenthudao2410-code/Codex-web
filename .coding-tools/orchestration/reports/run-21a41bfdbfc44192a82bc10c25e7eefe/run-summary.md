# Orchestration Run Summary

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Task: `753fb8a8518741bea02625b689eee869`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Status: **accepted**
- Started: `2026-09-03T07:35:05.275Z`
- Finished: `2026-09-03T09:49:49.185Z`

## Outcome metrics

- Waves: **14**
- Route decisions: **14**
- Failures observed: **14**
- REPLAN transitions: **14**
- Proof stages: **13**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `4852a799b1fc4532a34525ea42f53417` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `46c2e05e07604ea68f4f928dde32ce68` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `f9b6d34f60be441ea7e68786ff8237cb` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 4 | `1c1580a02cc84d78a06fd366fa28726f` | 4 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 5 | `0f2011a7fa93446394764d5f35b11348` | 5 | `replan_request` | `deep_single_lane` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 6 | `19f1e9934133423a8f729e0b6cf301d4` | 6 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 7 | `18a05fc6ad584af3852cc8cabb9bcfc9` | 7 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 8 | `d8275650b9f240b99be1b47c09ad7561` | 8 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 9 | `452c791e3e7e4c23a5b16d9deac17eab` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 10 | `a3d5679bd4134d33915fc8b3b151a3f6` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 11 | `7fa4abbba2364b0aa956204daf1f12b0` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 12 | `d64c8011abee4c54bdeda0be17ab7b12` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 13 | `02e9f6b139494c548cd3f2a8d628cd4c` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 14 | `f79061ca03244aa6b68055fe5469351e` | 9 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 5eb2508a28d84d958a1ef7a69283b1a5 | f79061ca03244aa6b68055fe5469351e | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | ec7e322b0ee750c89069196850efd97558a6032807c2d135a3797476c357fa9e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36688 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36744 | `deterministic` | `deterministic` | explicit_request |
| 36777 | `deterministic` | `deterministic` | explicit_request |
| 36846 | `deterministic` | `deterministic` | explicit_request |
| 36895 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 36943 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36966 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36998 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37014 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37044 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37068 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37096 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37136 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 37167 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 36728 | `SOL_REJECTED` | `ACCEPTING` | Reject stale v8 proof fail-closed: current exact bytes of all three v8 closure files drifted after proof, so proof fingerprint 8ac7c5c9... cannot support final acceptance. Preserve current source; replan as exact six-file adoption plus fresh proof. |
| 36764 | `SOL_REJECTED` | `ACCEPTING` | Wave proof is invalid for final acceptance because automatic verification ran out-of-scope commands `npm run test` and `npm run dist`; the latter created build/package artifacts under dist/win-unpacked before being terminated by supported command_control. Preserve all generated artifacts untouched and exclude them from acceptance. Replace proof 1fd4dee62a314933a4de93c6110e36df with fresh proof using only the operator-approved three commands, preserving current source bytes and unrelated dirty work. |
| 36792 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 36882 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 36902 | `PROMPT_TOO_LARGE` | `ROUTED` |  |
| 36959 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 36986 | `SOL_REJECTED` | `ACCEPTING` | Reject incomplete acceptance oracle/scope. Current v6 host-observation authority and fixtures are good, but approved closure is not complete: chatEvaluationJournal.js still uses generic Object.values traversal; controller_usage_ingress lacks strict provenance/RUN-WAVE/turn-trace and checkpointed active-lease guards; Electron controllerUsage lacks exact RUN/WAVE fields; controller usage validation lacks safe-integer/run-wave binding closure. Proof also omitted git diff --check, test_stateless_http_2026.py, test_usage_accounting_v2.py, and test_accepted_result_economics_report.py. Preserve the four valid v6 changes and replan same RUN only. |
| 37007 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 37035 | `SOL_REJECTED` | `ACCEPTING` | Semantic acceptance rejected despite passing focused proof: deferred controller usage with missing run_id/wave_id is currently keyed only by agent_workflow name, so an existing authoritative RUN can consume an incomplete pre-dispatch report. Requirement is fail-closed once RUN/WAVE authority already exists; deferred binding is allowed only when no authority existed before prevalidation and the exact RUN/WAVE is created by that same first agent_workflow request. Preserve all already-correct v6 authority, allowlisted observer, provenance, correlation, safe-integer, lease, and test changes; replan same RUN only for this bounded deferred-binding guard and regression coverage. |
| 37059 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 37084 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 37111 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 37152 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 37192 | `SOL_REJECTED` | `ACCEPTING` | Reject semantic regression despite passing focused proof: mcp_http_handler.py reintroduced a global runtime.task_state predispatch_orchestration_authority gate and early missing-run_id rejection. That violates the explicitly authorized repair because a fresh stateless task_context must not inherit another task context's orchestration authority. Preserve all other valid packet changes. Replan same RUN only to derive existing-authority from the exact stateless task context/request-local binding and keep deferred first-agent binding fail-closed without global projection or clock heuristics. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
