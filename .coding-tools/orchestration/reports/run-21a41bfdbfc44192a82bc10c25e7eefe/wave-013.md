# Orchestration Wave 13

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `02e9f6b139494c548cd3f2a8d628cd4c`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Objective revision: `9`
- Objective SHA-256: `a50b4d2c65e30afc07f47f509306c3f0337fc28596f8396721d7ef8b705e7234`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `9b02f8d65c87552719db1470d6c763f46fd1c8309d314fa1c164b3a075d0ac85`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37114 | 2026-09-03T09:42:42.718Z | wave_replanned |  | PREFLIGHT | reason=Fresh proof changed the evidence: the existing-run regression no longer appears as the failing test, but the valid first agent_workflow deferred-usage test now receives a JSON-RPC error. The predispatch authority guard is therefore over-classifying a first-use task context. Distinguish authority that existed before this request from state materialized while resolving/binding the first request, preserving fail-closed rejection for truly pre-existing RUN/WAVE and preserving valid first-agent_workflow deferred binding. |
| 37115 | 2026-09-03T09:42:42.951Z | observation_span_recorded |  |  |  |
| 37116 | 2026-09-03T09:42:44.682Z | observation_span_recorded |  |  |  |
| 37117 | 2026-09-03T09:42:44.898Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37118 | 2026-09-03T09:42:49.751Z | managed_process_admitted |  |  | owner=chatweb-handler-minimal-inspect |
| 37119 | 2026-09-03T09:42:50.008Z | managed_process_started |  |  | owner=chatweb-handler-minimal-inspect |
| 37120 | 2026-09-03T09:42:50.774Z | managed_process_terminal |  |  | owner=chatweb-handler-minimal-inspect |
| 37121 | 2026-09-03T09:43:21.925Z | managed_process_admitted |  |  | owner=chatweb-handler-repin |
| 37122 | 2026-09-03T09:43:22.251Z | managed_process_started |  |  | owner=chatweb-handler-repin |
| 37123 | 2026-09-03T09:43:23.790Z | managed_process_terminal |  |  | owner=chatweb-handler-repin |
| 37124 | 2026-09-03T09:43:44.340Z | managed_process_admitted |  |  | owner=chatweb-run21a-first-use-proof |
| 37125 | 2026-09-03T09:43:44.692Z | managed_process_started |  |  | owner=chatweb-run21a-first-use-proof |
| 37126 | 2026-09-03T09:43:47.047Z | managed_process_terminal |  |  | owner=chatweb-run21a-first-use-proof |
| 37127 | 2026-09-03T09:43:59.274Z | managed_process_admitted |  |  | owner=chatweb-run21a-ingress-read |
| 37128 | 2026-09-03T09:43:59.573Z | managed_process_started |  |  | owner=chatweb-run21a-ingress-read |
| 37129 | 2026-09-03T09:44:00.215Z | managed_process_terminal |  |  | owner=chatweb-run21a-ingress-read |
| 37134 | 2026-09-03T09:45:16.555Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37135 | 2026-09-03T09:45:16.722Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37136 | 2026-09-03T09:45:16.926Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 37137 | 2026-09-03T09:45:17.105Z | state_transition | READY | ROUTED | reason=route_selected |
| 37138 | 2026-09-03T09:45:17.326Z | observation_span_recorded |  |  |  |
| 37139 | 2026-09-03T09:45:18.580Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=afbf7d9a1cb545c3a6c1d85fd108fbd5 |
| 37140 | 2026-09-03T09:45:18.772Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37141 | 2026-09-03T09:45:19.749Z | existing_file_adoption_observed |  |  |  |
| 37142 | 2026-09-03T09:45:20.011Z | patch_surface_observed |  |  |  |
| 37143 | 2026-09-03T09:45:20.267Z | observation_span_recorded |  |  |  |
| 37144 | 2026-09-03T09:45:20.584Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=afbf7d9a1cb545c3a6c1d85fd108fbd5 |
| 37145 | 2026-09-03T09:45:20.759Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37146 | 2026-09-03T09:45:22.083Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=7e6576d404d588269e33185e5da4be927d755ff8818ea8446978b93f5572b62e |
| 37147 | 2026-09-03T09:45:22.494Z | managed_process_admitted |  |  | owner=default |
| 37148 | 2026-09-03T09:45:22.798Z | managed_process_started |  |  | owner=default |
| 37149 | 2026-09-03T09:46:01.437Z | managed_process_terminal |  |  | owner=default |
| 37150 | 2026-09-03T09:46:01.867Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=7e6576d404d588269e33185e5da4be927d755ff8818ea8446978b93f5572b62e |
| 37151 | 2026-09-03T09:46:02.076Z | observation_span_recorded |  |  |  |
| 37152 | 2026-09-03T09:46:02.276Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 37153 | 2026-09-03T09:46:02.494Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 37154 | 2026-09-03T09:46:02.743Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 7e6576d404d588269e33185e5da4be927d755ff8818ea8446978b93f5572b62e | False | 39469 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
