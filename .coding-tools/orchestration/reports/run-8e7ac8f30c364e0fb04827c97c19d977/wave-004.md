# Orchestration Wave 4

- Run: `8e7ac8f30c364e0fb04827c97c19d977`
- Wave: `63e44ad0f1184917970a26b0ba6122be`
- Objective: Localize the single failing static contract assertion after the Roaming recovery-supervisor patch. Determine whether the implementation is wrong or the assertion is over-specific. Do not mutate files.
- Objective revision: `4`
- Objective SHA-256: `79aca976fe22d8124b03462111c51535504a50b929915a896073fdeb348a6237`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `5e3fabb6f72df6c45f2a4d7908bb5f75b1ae7e9ad682c054125112c6d8e7126c`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57982 | 2026-09-15T07:44:29.819Z | wave_replanned |  | PREFLIGHT | reason=The failed proof shows exactly one static assertion failure. Inspect the current implementation and assertion before choosing the smallest corrective mutation. |
| 57983 | 2026-09-15T07:44:30.079Z | observation_span_recorded |  |  |  |
| 57984 | 2026-09-15T07:44:35.734Z | observation_span_recorded |  |  |  |
| 57985 | 2026-09-15T07:44:35.921Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57986 | 2026-09-15T07:45:07.759Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57987 | 2026-09-15T07:45:08.009Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57988 | 2026-09-15T07:45:08.214Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 57989 | 2026-09-15T07:45:08.423Z | state_transition | READY | ROUTED | reason=route_selected |
| 57990 | 2026-09-15T07:45:08.704Z | observation_span_recorded |  |  |  |
| 57991 | 2026-09-15T07:45:09.397Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e7881c4564e74cdcaf2861006999e2c3 |
| 57992 | 2026-09-15T07:45:09.621Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57993 | 2026-09-15T07:45:10.332Z | patch_surface_observed |  |  |  |
| 57994 | 2026-09-15T07:45:10.620Z | observation_span_recorded |  |  |  |
| 57995 | 2026-09-15T07:45:11.187Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e7881c4564e74cdcaf2861006999e2c3 |
| 57996 | 2026-09-15T07:45:11.389Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57997 | 2026-09-15T07:45:11.969Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=892990209b3fe41e0598ff7165f5cafb611d58d3a8f070e42a608c7a3ff453a8 |
| 57998 | 2026-09-15T07:45:12.438Z | managed_process_admitted |  |  | owner=default |
| 57999 | 2026-09-15T07:45:12.787Z | managed_process_started |  |  | owner=default |
| 58000 | 2026-09-15T07:45:39.493Z | managed_process_terminal |  |  | owner=default |
| 58001 | 2026-09-15T07:45:41.494Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=892990209b3fe41e0598ff7165f5cafb611d58d3a8f070e42a608c7a3ff453a8 |
| 58002 | 2026-09-15T07:45:42.502Z | observation_span_recorded |  |  |  |
| 58003 | 2026-09-15T07:45:42.694Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 58004 | 2026-09-15T07:45:42.895Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 58037 | 2026-09-15T07:48:02.198Z | continuity_telemetry_recorded |  |  |  |
| 58038 | 2026-09-15T07:48:25.729Z | managed_process_admitted |  |  | owner=default |
| 58039 | 2026-09-15T07:48:26.113Z | managed_process_started |  |  | owner=default |
| 58040 | 2026-09-15T07:48:27.547Z | managed_process_terminal |  |  | owner=default |
| 58041 | 2026-09-15T07:48:54.081Z | observation_span_recorded |  |  |  |
| 58042 | 2026-09-15T07:48:54.347Z | failure_observed | ACCEPTING | ACCEPTING | reason=Replan required only for acceptance lineage: recovery-supervisor.ps1 was pre-existing dirty at this wave start and therefore was not proven inside this wave's write lease. The focused tests are green, but source bytes must be exact-byte adopted into a new wave before controller acceptance.; failure_class=SOL_REJECTED |
| 58043 | 2026-09-15T07:48:54.556Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 58044 | 2026-09-15T07:48:54.822Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58068 | 2026-09-15T07:50:45.373Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 892990209b3fe41e0598ff7165f5cafb611d58d3a8f070e42a608c7a3ff453a8 | False | 29015 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `9f60fdae5283de9c93f97921c9edbdd993758d31b935a527da1eeff6f051481f`
