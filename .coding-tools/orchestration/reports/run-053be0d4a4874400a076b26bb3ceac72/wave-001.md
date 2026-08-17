# Orchestration Wave 1

- Run: `053be0d4a4874400a076b26bb3ceac72`
- Wave: `adbd58a364124a8f8d0ef3cb0d432cf1`
- Objective: Implement Python-side compute-first measurement hardening only, preserving all unrelated staged/unstaged changes exactly. Do NOT modify docs/PRODUCTION_CLOSURE_ROLLOUT.md, resources/recovery-supervisor, tests/recovery-supervisor.test.js, installer/Recovery/activation/release surfaces, or external system state. In resources/coding-tools-mcp: (1) bump evaluation schema version and add explicit experiment_kind separating model_routing from compute_placement while keeping backward-compatible model_routing semantics for historical rows; include experiment_kind in causal pair identity/fingerprint and prevent cross-domain pairing. (2) Add task_control action=controller_observation with a durable cumulative content-free controller snapshot contract: source, optional clock_domain, started_at/ended_at informational timestamps, same-clock duration_ms, explicitly measured pre_mcp_ms, cumulative monetary_cost and token counters. Validate cumulative counters/cost/durations never decrease; unknown remains unknown, never synthesize zero. accepted_result_evaluation must merge delayed observations over run-creation controller metadata and must NOT derive pre_mcp_ms by subtracting controller/server wall timestamps across clock domains. (3) Add task_control action=placement with a durable content-free compute placement observation: source, policy local_only/server_preferred, policy_version, source_mode, resource_class, actual_placement local/remote, reason_code, dispatch_attempted, dispatch_succeeded, fallback, selected_runner_id/tool_name/job_id optional. accepted_result_evaluation returns latest placement. For experiment_kind=compute_placement, pairing_eligible requires actual placement evidence and policy match. (4) Strengthen paired evaluation quality floor: accepted + explicit oracle_pass=true + known zero critical defects, and fail for regression_escape/rollback_required/manual_fix_required/maintainability_gate=fail when present. Compute Pareto relation only when both pair rows pass quality and accepted-result TTAR plus total monetary cost are complete; do not use weighted scores. Expose routing_regret only for model_routing and placement_regret only through a dedicated paired_compute_placement_evaluation wrapper with baseline local_only vs candidate server_preferred; tradeoffs/insufficient evidence remain indeterminate. automatic_activation must remain false. (5) Add focused tests for delayed cumulative controller observations, monotonicity rejection, cross-clock pre_mcp semantics, experiment isolation, compute-placement evidence requirement, explicit quality floor, Pareto dominance/regret/tradeoff, task_control handlers/schema, and preservation of synthetic/benchmark exclusion. Do not change public top-level tool count.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12593 | 2026-08-17T08:29:26.521Z | run_started |  | PREFLIGHT |  |
| 12594 | 2026-08-17T08:29:27.310Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12595 | 2026-08-17T08:29:27.682Z | managed_process_admitted |  |  | owner=default |
| 12596 | 2026-08-17T08:29:28.110Z | managed_process_started |  |  | owner=default |
| 12614 | 2026-08-17T08:30:13.718Z | managed_process_terminal |  |  | owner=default |
| 12615 | 2026-08-17T08:30:13.906Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12616 | 2026-08-17T08:30:14.087Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12617 | 2026-08-17T08:30:14.334Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12618 | 2026-08-17T08:30:14.802Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12619 | 2026-08-17T08:30:15.013Z | state_transition | READY | ROUTED | reason=route_selected |
| 12620 | 2026-08-17T08:30:15.930Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=fae9506d47a84f3e98cdcb7ddc422617 |
| 12621 | 2026-08-17T08:30:16.129Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12622 | 2026-08-17T08:30:16.854Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=fae9506d47a84f3e98cdcb7ddc422617 |
| 12623 | 2026-08-17T08:30:17.111Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12624 | 2026-08-17T08:30:17.567Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5e13c83f6d0986db7bba9c16dcca5d67f4ef89df5c979bb06e9311c75f2eda7f |
| 12625 | 2026-08-17T08:30:18.025Z | managed_process_admitted |  |  | owner=default |
| 12626 | 2026-08-17T08:30:18.361Z | managed_process_started |  |  | owner=default |
| 12627 | 2026-08-17T08:31:02.760Z | managed_process_terminal |  |  | owner=default |
| 12628 | 2026-08-17T08:31:04.105Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5e13c83f6d0986db7bba9c16dcca5d67f4ef89df5c979bb06e9311c75f2eda7f |
| 12629 | 2026-08-17T08:31:04.415Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12668 | 2026-08-17T08:38:13.460Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12669 | 2026-08-17T08:38:13.802Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12670 | 2026-08-17T08:38:14.403Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12671 | 2026-08-17T08:38:24.747Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12672 | 2026-08-17T08:38:25.064Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12673 | 2026-08-17T08:38:25.687Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12674 | 2026-08-17T08:38:38.234Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12675 | 2026-08-17T08:38:38.591Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12676 | 2026-08-17T08:38:39.453Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12677 | 2026-08-17T08:38:48.713Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12678 | 2026-08-17T08:38:49.030Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12679 | 2026-08-17T08:38:49.613Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12680 | 2026-08-17T08:39:03.797Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12681 | 2026-08-17T08:39:04.130Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12682 | 2026-08-17T08:39:04.582Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12683 | 2026-08-17T08:39:24.073Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12684 | 2026-08-17T08:39:24.321Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12685 | 2026-08-17T08:39:24.741Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12686 | 2026-08-17T08:39:34.399Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12687 | 2026-08-17T08:39:34.697Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12688 | 2026-08-17T08:39:35.137Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12689 | 2026-08-17T08:40:15.978Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12690 | 2026-08-17T08:40:16.305Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 5e13c83f6d0986db7bba9c16dcca5d67f4ef89df5c979bb06e9311c75f2eda7f | False | 45968 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e45e225f8f2845c28b6fb071d82019a7 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | dc6129ed3187918223add8878fd723fc5cbd0daf85f1fcc7b50aec97e48adc79 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `305f2042513c3c5e1773a83eea16032d6cb3a2cd223c41204e06ad4390552f9a`
