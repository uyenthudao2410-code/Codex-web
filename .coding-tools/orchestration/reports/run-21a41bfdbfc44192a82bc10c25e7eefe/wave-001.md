# Orchestration Wave 1

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `4852a799b1fc4532a34525ea42f53417`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Objective revision: `1`
- Objective SHA-256: `a50b4d2c65e30afc07f47f509306c3f0337fc28596f8396721d7ef8b705e7234`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `85652f5dae152f5e2d65ce138b4674f162dc93489806c9e48fced33ac63e2415`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36683 | 2026-09-03T07:35:06.427Z | run_started |  | PREFLIGHT |  |
| 36684 | 2026-09-03T07:35:08.390Z | observation_span_recorded |  |  |  |
| 36685 | 2026-09-03T07:35:35.017Z | solution_shadow_recommended |  |  |  |
| 36686 | 2026-09-03T07:35:35.162Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36687 | 2026-09-03T07:35:35.371Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36688 | 2026-09-03T07:35:35.552Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36689 | 2026-09-03T07:35:35.717Z | state_transition | READY | ROUTED | reason=route_selected |
| 36690 | 2026-09-03T07:35:35.917Z | observation_span_recorded |  |  |  |
| 36691 | 2026-09-03T07:35:36.965Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=349600b9d8b445808a87b4b06ba239a9 |
| 36692 | 2026-09-03T07:35:37.149Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36693 | 2026-09-03T07:35:38.375Z | patch_surface_observed |  |  |  |
| 36694 | 2026-09-03T07:35:38.607Z | observation_span_recorded |  |  |  |
| 36695 | 2026-09-03T07:35:38.900Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=349600b9d8b445808a87b4b06ba239a9 |
| 36696 | 2026-09-03T07:35:39.065Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36697 | 2026-09-03T07:35:40.121Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7168755c3497c18b; input_fingerprint=c77a6d736e6c0aee640c2776fa202caa815aaa25a4d7556131dfc75ce947dfcd |
| 36698 | 2026-09-03T07:35:40.488Z | managed_process_admitted |  |  | owner=default |
| 36699 | 2026-09-03T07:35:40.826Z | managed_process_started |  |  | owner=default |
| 36700 | 2026-09-03T07:35:41.339Z | managed_process_terminal |  |  | owner=default |
| 36701 | 2026-09-03T07:35:41.726Z | proof_recorded |  |  | stage_id=check:7168755c3497c18b; status=passed; cache_hit=False; input_fingerprint=c77a6d736e6c0aee640c2776fa202caa815aaa25a4d7556131dfc75ce947dfcd |
| 36702 | 2026-09-03T07:35:41.946Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f3e988cfc8f452bec263f588d6141ce1ed454275b2e3f302b36787df66b43873 |
| 36703 | 2026-09-03T07:35:42.352Z | managed_process_admitted |  |  | owner=default |
| 36704 | 2026-09-03T07:35:42.702Z | managed_process_started |  |  | owner=default |
| 36705 | 2026-09-03T07:35:46.039Z | managed_process_terminal |  |  | owner=default |
| 36706 | 2026-09-03T07:35:53.166Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f3e988cfc8f452bec263f588d6141ce1ed454275b2e3f302b36787df66b43873 |
| 36707 | 2026-09-03T07:35:54.758Z | observation_span_recorded |  |  |  |
| 36708 | 2026-09-03T07:35:54.940Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 36709 | 2026-09-03T07:41:01.938Z | managed_process_admitted |  |  | owner=default |
| 36710 | 2026-09-03T07:41:02.255Z | managed_process_started |  |  | owner=default |
| 36711 | 2026-09-03T07:41:02.917Z | managed_process_terminal |  |  | owner=default |
| 36712 | 2026-09-03T07:50:21.415Z | managed_process_admitted |  |  | owner=chatweb |
| 36713 | 2026-09-03T07:50:21.757Z | managed_process_started |  |  | owner=chatweb |
| 36714 | 2026-09-03T07:50:22.450Z | managed_process_terminal |  |  | owner=chatweb |
| 36715 | 2026-09-03T07:50:34.305Z | managed_process_admitted |  |  | owner=chatweb |
| 36716 | 2026-09-03T07:50:34.624Z | managed_process_started |  |  | owner=chatweb |
| 36717 | 2026-09-03T07:50:35.072Z | managed_process_terminal |  |  | owner=chatweb |
| 36718 | 2026-09-03T07:50:57.594Z | managed_process_admitted |  |  | owner=chatweb |
| 36719 | 2026-09-03T07:50:57.886Z | managed_process_started |  |  | owner=chatweb |
| 36720 | 2026-09-03T07:50:58.353Z | managed_process_terminal |  |  | owner=chatweb |
| 36721 | 2026-09-03T07:51:12.458Z | managed_process_admitted |  |  | owner=chatweb |
| 36722 | 2026-09-03T07:51:12.856Z | managed_process_started |  |  | owner=chatweb |
| 36723 | 2026-09-03T07:51:13.873Z | managed_process_terminal |  |  | owner=chatweb |
| 36724 | 2026-09-03T07:51:46.062Z | managed_process_admitted |  |  | owner=chatweb |
| 36725 | 2026-09-03T07:51:46.409Z | managed_process_started |  |  | owner=chatweb |
| 36726 | 2026-09-03T07:51:47.176Z | managed_process_terminal |  |  | owner=chatweb |
| 36727 | 2026-09-03T07:52:07.784Z | observation_span_recorded |  |  |  |
| 36728 | 2026-09-03T07:52:08.042Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject stale v8 proof fail-closed: current exact bytes of all three v8 closure files drifted after proof, so proof fingerprint 8ac7c5c9... cannot support final acceptance. Preserve current source; replan as exact six-file adoption plus fresh proof.; failure_class=SOL_REJECTED |
| 36729 | 2026-09-03T07:52:08.237Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 36730 | 2026-09-03T07:52:08.430Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7168755c3497c18b | passed | c77a6d736e6c0aee640c2776fa202caa815aaa25a4d7556131dfc75ce947dfcd | False | 1249 | 0 |
| verify:tests | passed | f3e988cfc8f452bec263f588d6141ce1ed454275b2e3f302b36787df66b43873 | False | 10797 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
