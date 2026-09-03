# Orchestration Wave 14

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `f79061ca03244aa6b68055fe5469351e`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Objective revision: `9`
- Objective SHA-256: `a50b4d2c65e30afc07f47f509306c3f0337fc28596f8396721d7ef8b705e7234`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `b0a4ae131b4a2c75c57f48c09e1ba7aef171b4c154e31eb2432b43bf3cad2669`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37155 | 2026-09-03T09:46:39.561Z | wave_replanned |  | PREFLIGHT | reason=Exact typed proof shows the only remaining failure is a valid first agent_workflow being false-rejected by comparing full-precision prevalidation time against millisecond-serialized run.created_at. Timestamp proximity must not establish orchestration authority. Remove the deferred timestamp marker/helper/check and rely on the stronger causal chain already present: request-scoped predispatch orchestration projection must be empty for deferred usage; the same agent_workflow response must return the exact current RUN/WAVE; and server-owned host turn/trace must match. Preserve fail-closed rejection when authority already existed and preserve all unrelated current bytes. |
| 37156 | 2026-09-03T09:46:39.845Z | observation_span_recorded |  |  |  |
| 37157 | 2026-09-03T09:46:41.794Z | observation_span_recorded |  |  |  |
| 37158 | 2026-09-03T09:46:41.979Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37159 | 2026-09-03T09:47:04.513Z | managed_process_admitted |  |  | owner=chatweb-deferred-phase-replan |
| 37160 | 2026-09-03T09:47:04.839Z | managed_process_started |  |  | owner=chatweb-deferred-phase-replan |
| 37161 | 2026-09-03T09:47:05.948Z | managed_process_terminal |  |  | owner=chatweb-deferred-phase-replan |
| 37162 | 2026-09-03T09:47:22.018Z | managed_process_admitted |  |  | owner=chatweb-deferred-final-hashes |
| 37163 | 2026-09-03T09:47:22.442Z | managed_process_started |  |  | owner=chatweb-deferred-final-hashes |
| 37164 | 2026-09-03T09:47:24.228Z | managed_process_terminal |  |  | owner=chatweb-deferred-final-hashes |
| 37165 | 2026-09-03T09:47:26.083Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37166 | 2026-09-03T09:47:26.225Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37167 | 2026-09-03T09:47:26.441Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 37168 | 2026-09-03T09:47:26.691Z | state_transition | READY | ROUTED | reason=route_selected |
| 37169 | 2026-09-03T09:47:26.914Z | observation_span_recorded |  |  |  |
| 37170 | 2026-09-03T09:47:28.028Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7ab902edaf4b413c958c102c1dcace02 |
| 37171 | 2026-09-03T09:47:28.229Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37172 | 2026-09-03T09:47:29.733Z | patch_surface_observed |  |  |  |
| 37173 | 2026-09-03T09:47:29.930Z | observation_span_recorded |  |  |  |
| 37174 | 2026-09-03T09:47:30.243Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7ab902edaf4b413c958c102c1dcace02 |
| 37175 | 2026-09-03T09:47:30.444Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37176 | 2026-09-03T09:47:31.612Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=992dbac7bb47f39ccdcb2712ad0c47ee5059a8e2d42197ade31a0272044b40b8 |
| 37177 | 2026-09-03T09:47:32.026Z | managed_process_admitted |  |  | owner=default |
| 37178 | 2026-09-03T09:47:32.343Z | managed_process_started |  |  | owner=default |
| 37179 | 2026-09-03T09:48:08.602Z | managed_process_terminal |  |  | owner=default |
| 37180 | 2026-09-03T09:48:09.658Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=992dbac7bb47f39ccdcb2712ad0c47ee5059a8e2d42197ade31a0272044b40b8 |
| 37181 | 2026-09-03T09:48:10.991Z | observation_span_recorded |  |  |  |
| 37182 | 2026-09-03T09:48:11.172Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37183 | 2026-09-03T09:49:22.520Z | managed_process_admitted |  |  | owner=chatweb-run21a-final-semantic-review |
| 37184 | 2026-09-03T09:49:22.937Z | managed_process_started |  |  | owner=chatweb-run21a-final-semantic-review |
| 37185 | 2026-09-03T09:49:24.653Z | managed_process_terminal |  |  | owner=chatweb-run21a-final-semantic-review |
| 37186 | 2026-09-03T09:49:36.903Z | managed_process_admitted |  |  | owner=chatweb-run21a-accept-hash |
| 37187 | 2026-09-03T09:49:37.210Z | managed_process_started |  |  | owner=chatweb-run21a-accept-hash |
| 37188 | 2026-09-03T09:49:37.870Z | managed_process_terminal |  |  | owner=chatweb-run21a-accept-hash |
| 37189 | 2026-09-03T09:49:49.003Z | quality_outcome_recorded |  |  |  |
| 37190 | 2026-09-03T09:49:49.185Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 37191 | 2026-09-03T09:49:49.584Z | observation_span_recorded |  |  |  |
| 37192 | 2026-09-03T09:49:49.808Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject semantic regression despite passing focused proof: mcp_http_handler.py reintroduced a global runtime.task_state predispatch_orchestration_authority gate and early missing-run_id rejection. That violates the explicitly authorized repair because a fresh stateless task_context must not inherit another task context's orchestration authority. Preserve all other valid packet changes. Replan same RUN only to derive existing-authority from the exact stateless task context/request-local binding and keep deferred first-agent binding fail-closed without global projection or clock heuristics.; failure_class=SOL_REJECTED |
| 37193 | 2026-09-03T09:49:49.985Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 37194 | 2026-09-03T09:49:50.214Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 37195 | 2026-09-03T09:49:50.454Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 992dbac7bb47f39ccdcb2712ad0c47ee5059a8e2d42197ade31a0272044b40b8 | False | 37750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5eb2508a28d84d958a1ef7a69283b1a5 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | ec7e322b0ee750c89069196850efd97558a6032807c2d135a3797476c357fa9e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
