# Orchestration Wave 9

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `452c791e3e7e4c23a5b16d9deac17eab`
- Objective: Finish and prove the already-applied H0/L3 ChatWeb controller usage sideband. Keep the existing structured-response numeric-only observer, turn/trace RUN/WAVE correlation, authenticated ChatWeb controllerUsage carrier, and immediate CHECKPOINTED post-turn ingress. Close only the remaining causal gaps: update the JS tests to the new two-phase correlation/controller-usage semantics and advance evaluation_report host-observation schema consumption from v5 to v6 while retaining v5 as legacy evidence. Do not alter unrelated dirty work.
- Objective revision: `9`
- Objective SHA-256: `a50b4d2c65e30afc07f47f509306c3f0337fc28596f8396721d7ef8b705e7234`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `f8e54e7051a8a08ec30c4eb11d1c0fb10440337e0c86ea7b433b700ac7f04efc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37010 | 2026-09-03T09:29:01.757Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance rejected WAVE 18a05fc6ad584af3852cc8cabb9bcfc9 because schema-v6 proof was green but the H0/L3 acceptance oracle and hardening scope remained incomplete: generic Object.values traversal, missing exact RUN/WAVE controller metadata, weak provenance/RUN-WAVE/turn-trace validation, no read-only CHECKPOINTED lease guard, no JavaScript-safe integer closure, and omitted diff/stateless/accounting/economics proofs. Preserve the already-green schema-v6 changes and create exactly one new deterministic mcp_only wave for these rejected causal gaps only. |
| 37011 | 2026-09-03T09:29:01.994Z | observation_span_recorded |  |  |  |
| 37012 | 2026-09-03T09:29:02.260Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37013 | 2026-09-03T09:29:02.436Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37014 | 2026-09-03T09:29:02.596Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 37015 | 2026-09-03T09:29:02.744Z | state_transition | READY | ROUTED | reason=route_selected |
| 37016 | 2026-09-03T09:29:02.961Z | observation_span_recorded |  |  |  |
| 37017 | 2026-09-03T09:29:04.355Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=35bdb21ace5f4a21ac42030ab6681d6c |
| 37018 | 2026-09-03T09:29:04.507Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37019 | 2026-09-03T09:29:05.900Z | patch_surface_observed |  |  |  |
| 37020 | 2026-09-03T09:29:06.084Z | patch_surface_observed |  |  |  |
| 37021 | 2026-09-03T09:29:06.290Z | patch_surface_observed |  |  |  |
| 37022 | 2026-09-03T09:29:06.459Z | patch_surface_observed |  |  |  |
| 37023 | 2026-09-03T09:29:06.665Z | patch_surface_observed |  |  |  |
| 37024 | 2026-09-03T09:29:06.864Z | observation_span_recorded |  |  |  |
| 37025 | 2026-09-03T09:29:07.164Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=35bdb21ace5f4a21ac42030ab6681d6c |
| 37026 | 2026-09-03T09:29:07.320Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37027 | 2026-09-03T09:29:08.706Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=7327e6360631da6d17e59440966b7c897068631a56e901722e2b73cd4a441740 |
| 37028 | 2026-09-03T09:29:09.223Z | managed_process_admitted |  |  | owner=default |
| 37029 | 2026-09-03T09:29:09.557Z | managed_process_started |  |  | owner=default |
| 37030 | 2026-09-03T09:29:52.363Z | managed_process_terminal |  |  | owner=default |
| 37031 | 2026-09-03T09:29:53.533Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=7327e6360631da6d17e59440966b7c897068631a56e901722e2b73cd4a441740 |
| 37032 | 2026-09-03T09:29:54.743Z | observation_span_recorded |  |  |  |
| 37033 | 2026-09-03T09:29:55.185Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37034 | 2026-09-03T09:34:14.509Z | observation_span_recorded |  |  |  |
| 37035 | 2026-09-03T09:34:14.704Z | failure_observed | ACCEPTING | ACCEPTING | reason=Semantic acceptance rejected despite passing focused proof: deferred controller usage with missing run_id/wave_id is currently keyed only by agent_workflow name, so an existing authoritative RUN can consume an incomplete pre-dispatch report. Requirement is fail-closed once RUN/WAVE authority already exists; deferred binding is allowed only when no authority existed before prevalidation and the exact RUN/WAVE is created by that same first agent_workflow request. Preserve all already-correct v6 authority, allowlisted observer, provenance, correlation, safe-integer, lease, and test changes; replan same RUN only for this bounded deferred-binding guard and regression coverage.; failure_class=SOL_REJECTED |
| 37036 | 2026-09-03T09:34:14.892Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 37037 | 2026-09-03T09:34:15.113Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 7327e6360631da6d17e59440966b7c897068631a56e901722e2b73cd4a441740 | False | 44312 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
