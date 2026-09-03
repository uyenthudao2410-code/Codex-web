# Orchestration Wave 12

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `d64c8011abee4c54bdeda0be17ab7b12`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Objective revision: `9`
- Objective SHA-256: `a50b4d2c65e30afc07f47f509306c3f0337fc28596f8396721d7ef8b705e7234`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `eaa88c811a1c2878c808e95aafd0df8728cdedbc22e493c162b5b64350d74b54`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37087 | 2026-09-03T09:39:57.082Z | wave_replanned |  | PREFLIGHT | reason=The regression test correctly supplies task_context_id, but predispatch authority detection reads runtime.task_state before the stateless request-scoped TaskStateStore is selected. Materialize the existing Runtime/task-state scoping helpers and repair the handler to inspect the exact resolved task_context_id after request workspace scoping but before orchestration dispatch. Preserve the deferred first-agent_workflow path and all other current bytes. |
| 37088 | 2026-09-03T09:39:57.270Z | observation_span_recorded |  |  |  |
| 37089 | 2026-09-03T09:39:59.015Z | observation_span_recorded |  |  |  |
| 37090 | 2026-09-03T09:39:59.607Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37091 | 2026-09-03T09:40:20.944Z | managed_process_admitted |  |  | owner=chatweb-run21a-final-guard-read |
| 37092 | 2026-09-03T09:40:21.449Z | managed_process_started |  |  | owner=chatweb-run21a-final-guard-read |
| 37093 | 2026-09-03T09:40:22.010Z | managed_process_terminal |  |  | owner=chatweb-run21a-final-guard-read |
| 37094 | 2026-09-03T09:40:49.284Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37095 | 2026-09-03T09:40:49.444Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37096 | 2026-09-03T09:40:49.692Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 37097 | 2026-09-03T09:40:49.843Z | state_transition | READY | ROUTED | reason=route_selected |
| 37098 | 2026-09-03T09:40:50.079Z | observation_span_recorded |  |  |  |
| 37099 | 2026-09-03T09:40:51.304Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3e9ebc3051c94ea4a1c6a50bb86a598d |
| 37100 | 2026-09-03T09:40:51.504Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37101 | 2026-09-03T09:40:52.484Z | patch_surface_observed |  |  |  |
| 37102 | 2026-09-03T09:40:52.673Z | observation_span_recorded |  |  |  |
| 37103 | 2026-09-03T09:40:52.997Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3e9ebc3051c94ea4a1c6a50bb86a598d |
| 37104 | 2026-09-03T09:40:53.135Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37105 | 2026-09-03T09:40:54.058Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9b66f14c95ca840fd26a66e54447d18595eb0c8ac737e6d84b4df4aea5a59574 |
| 37106 | 2026-09-03T09:40:54.458Z | managed_process_admitted |  |  | owner=default |
| 37107 | 2026-09-03T09:40:54.810Z | managed_process_started |  |  | owner=default |
| 37108 | 2026-09-03T09:41:26.415Z | managed_process_terminal |  |  | owner=default |
| 37109 | 2026-09-03T09:41:26.843Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=9b66f14c95ca840fd26a66e54447d18595eb0c8ac737e6d84b4df4aea5a59574 |
| 37110 | 2026-09-03T09:41:27.006Z | observation_span_recorded |  |  |  |
| 37111 | 2026-09-03T09:41:27.239Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 37112 | 2026-09-03T09:41:27.417Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 37113 | 2026-09-03T09:41:27.708Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 9b66f14c95ca840fd26a66e54447d18595eb0c8ac737e6d84b4df4aea5a59574 | False | 32438 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
