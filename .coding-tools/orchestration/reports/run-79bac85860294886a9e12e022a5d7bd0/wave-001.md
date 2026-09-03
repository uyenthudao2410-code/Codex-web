# Orchestration Wave 1

- Run: `79bac85860294886a9e12e022a5d7bd0`
- Wave: `9b3501fb6ffe48b8aa4e0a828ee45d60`
- Objective: Continue W3 Provider UsageEvent Hardening on the exact active RUN/WAVE after the pre-write solution-shadow gate. Apply only the smallest missing causal changes: version derived-pricing provenance, make attribution status explicit, and add a known provider fixture that round-trips exact provider values/cost/provenance through the durable ledger and bounded analytics. Preserve existing normalization, W2 controller RUN+turn identity, provider terminal dedupe, unknown_not_zero, public 8-tool contract, and unrelated dirty work. No commit/push/restart/package/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `f108e72252e9599666620a32f81c0bcf3ebf851f031f78c7b8b735b4bfec037f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `a98758a32322b8feb3ffa70d439eb2ce391e9292e6bb0c93bf89efc3c0228647`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33672 | 2026-08-31T19:13:13.448Z | run_started |  | PREFLIGHT |  |
| 33673 | 2026-08-31T19:13:13.878Z | observation_span_recorded |  |  |  |
| 33674 | 2026-08-31T19:13:14.134Z | solution_shadow_recommended |  |  |  |
| 33675 | 2026-08-31T19:13:14.344Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33676 | 2026-08-31T19:13:14.543Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33677 | 2026-08-31T19:13:14.735Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 33678 | 2026-08-31T19:13:14.926Z | state_transition | READY | ROUTED | reason=route_selected |
| 33679 | 2026-08-31T19:13:15.147Z | observation_span_recorded |  |  |  |
| 33680 | 2026-08-31T19:13:15.927Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3e9b73a43b2d47f09789c11ace975896 |
| 33681 | 2026-08-31T19:13:16.127Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33682 | 2026-08-31T19:13:16.963Z | patch_surface_observed |  |  |  |
| 33683 | 2026-08-31T19:13:17.116Z | observation_span_recorded |  |  |  |
| 33684 | 2026-08-31T19:13:17.420Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3e9b73a43b2d47f09789c11ace975896 |
| 33685 | 2026-08-31T19:13:17.595Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33686 | 2026-08-31T19:13:18.249Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e9684cc762e4cc9f; input_fingerprint=9502fc98b49a1fba48ea1ce26b607296bb6d4403b640cf0c81fcd1c4d8caa169 |
| 33687 | 2026-08-31T19:13:18.577Z | managed_process_admitted |  |  | owner=default |
| 33688 | 2026-08-31T19:13:18.876Z | managed_process_started |  |  | owner=default |
| 33689 | 2026-08-31T19:13:19.283Z | managed_process_terminal |  |  | owner=default |
| 33690 | 2026-08-31T19:13:19.688Z | proof_recorded |  |  | stage_id=check:e9684cc762e4cc9f; status=passed; cache_hit=False; input_fingerprint=9502fc98b49a1fba48ea1ce26b607296bb6d4403b640cf0c81fcd1c4d8caa169 |
| 33691 | 2026-08-31T19:13:19.901Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a92ac7c664476c342f009ecb7c726f73b2d85aabd18da90ac19ee31a0904c189 |
| 33692 | 2026-08-31T19:13:20.377Z | managed_process_admitted |  |  | owner=default |
| 33693 | 2026-08-31T19:13:20.765Z | managed_process_started |  |  | owner=default |
| 33694 | 2026-08-31T19:13:21.924Z | managed_process_terminal |  |  | owner=default |
| 33695 | 2026-08-31T19:13:23.090Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a92ac7c664476c342f009ecb7c726f73b2d85aabd18da90ac19ee31a0904c189 |
| 33696 | 2026-08-31T19:13:23.908Z | observation_span_recorded |  |  |  |
| 33697 | 2026-08-31T19:13:24.123Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 33725 | 2026-08-31T19:36:33.561Z | managed_process_admitted |  |  | owner=default |
| 33726 | 2026-08-31T19:36:33.939Z | managed_process_started |  |  | owner=default |
| 33727 | 2026-08-31T19:36:34.494Z | managed_process_terminal |  |  | owner=default |
| 33728 | 2026-08-31T19:36:42.672Z | managed_process_admitted |  |  | owner=default |
| 33729 | 2026-08-31T19:36:42.680Z | managed_process_started |  |  | owner=default |
| 33730 | 2026-08-31T19:36:44.099Z | managed_process_terminal |  |  | owner=default |
| 33731 | 2026-08-31T19:36:58.787Z | quality_outcome_recorded |  |  |  |
| 33732 | 2026-08-31T19:36:58.984Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 33733 | 2026-08-31T19:36:59.256Z | observation_span_recorded |  |  |  |
| 33734 | 2026-08-31T19:36:59.499Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e9684cc762e4cc9f | passed | 9502fc98b49a1fba48ea1ce26b607296bb6d4403b640cf0c81fcd1c4d8caa169 | False | 1104 | 0 |
| verify:tests | passed | a92ac7c664476c342f009ecb7c726f73b2d85aabd18da90ac19ee31a0904c189 | False | 2702 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 7fd9d8a6322240ea8216b2e003156f9a | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 087a37694fe2b57fb420bf456bd503520663cf0227ad4aedeb4b59ca1ccaee29 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `e8ca129be8d0b8829c7d9a9bafc6b07152c457274c3b14d5091c2448ced14c25`
