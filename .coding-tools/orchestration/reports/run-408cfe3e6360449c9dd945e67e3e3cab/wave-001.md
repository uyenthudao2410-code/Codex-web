# Orchestration Wave 1

- Run: `408cfe3e6360449c9dd945e67e3e3cab`
- Wave: `4e31a917ff6640748afe1a08036d2a72`
- Objective: Repair only the final stale frozen-ChatGPT P4 regression fixture after scoped ChatWeb controller identity was introduced. In test_frozen_chatgpt_shadow_recovers_explicit_preflight_run_after_projection_drift, register the synthetic hub controller using runtime._hub_client_record_id(runtime.request_context.hub_client) instead of literal 'chatweb', preserving the same logical hub_client metadata and all production behavior. Run test_solution_economics.py and test_execution_hub_faults.py only. No production changes, no commit/push/restart.
- Mode: `mcp_only`
- Base HEAD: `359a5f231e1950e8d97303e0d2b798984c145fe6`
- Worktree fingerprint: `f6c4080f0b81a73603d05ef85b9297e5b641f0a30c5bec7c378cbe4326b07f59`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20650 | 2026-08-19T07:23:50.511Z | run_started |  | PREFLIGHT |  |
| 20651 | 2026-08-19T07:23:50.996Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20652 | 2026-08-19T07:23:51.158Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20653 | 2026-08-19T07:23:51.288Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20654 | 2026-08-19T07:23:51.455Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20655 | 2026-08-19T07:23:51.694Z | state_transition | READY | ROUTED | reason=route_selected |
| 20656 | 2026-08-19T07:23:52.088Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6093ca6de7a44fecb426a2e6ec480e0d |
| 20657 | 2026-08-19T07:23:52.233Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20658 | 2026-08-19T07:23:52.583Z | patch_surface_observed |  |  |  |
| 20659 | 2026-08-19T07:23:52.772Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6093ca6de7a44fecb426a2e6ec480e0d |
| 20660 | 2026-08-19T07:23:52.919Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20661 | 2026-08-19T07:23:53.249Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=897da35e8126748d434aae8fabde8aa7d27bc4fb8dd20b09c2a9c7e6eaa15e00 |
| 20662 | 2026-08-19T07:23:53.522Z | managed_process_admitted |  |  | owner=default |
| 20663 | 2026-08-19T07:23:53.766Z | managed_process_started |  |  | owner=default |
| 20664 | 2026-08-19T07:24:08.756Z | managed_process_terminal |  |  | owner=default |
| 20665 | 2026-08-19T07:24:09.005Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=897da35e8126748d434aae8fabde8aa7d27bc4fb8dd20b09c2a9c7e6eaa15e00 |
| 20666 | 2026-08-19T07:24:09.449Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 20667 | 2026-08-19T07:24:11.615Z | state_transition | ACCEPTING | ABORTED | reason=task_cleared |
| 20668 | 2026-08-19T07:24:11.912Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 897da35e8126748d434aae8fabde8aa7d27bc4fb8dd20b09c2a9c7e6eaa15e00 | False | 15484 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `053807c1fabf82b30de84d11335f11542ab27ebaa845582506a9973bac320fae`
