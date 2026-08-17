# P3 Server-First Paired Experiment Manifest — Frozen Pilot Contract

**Experiment ID:** `p3-server-first-pilot-v1`
**Manifest date:** 2026-08-18 (Asia/Bangkok)
**Status:** `FROZEN BEFORE REPRESENTATIVE TREATMENT`
**Methodology/source commit:** `41204dc6` (`Harden P1 ITT analysis before P3`)
**Baseline policy:** `LOCAL_FIRST_V1`
**Treatment policy:** `SERVER_FIRST_DETERMINISTIC_V1`
**Automatic activation:** `false`

This document is the preregistered contract for the first P3 server-first instrumentation pilot. It must be frozen and committed before any representative treatment outcome is inspected. The initial pilot is for instrumentation, variance, failure-mix, break-even and power-planning evidence only; it is not an automatic promotion gate.

## 1. Scientific question

Primary hypothesis:

> On representative tasks that are portable, exact-source reproducible and protected by an explicit strong oracle, `SERVER_FIRST_DETERMINISTIC_V1` reduces accepted-result latency and local machine burden relative to `LOCAL_FIRST_V1` without degrading acceptance, first-pass behavior, repair trajectory, correctness, security, authority, robustness or compatibility.

The treatment dimension is **compute placement only**. Model routing is not part of this experiment and remains evidence-gated/fail-closed.

## 2. Frozen experiment contract

```yaml
experiment_id: p3-server-first-pilot-v1
phase: P3
study_type: paired_instrumentation_pilot
pilot_target_pairs:
  min: 10
  max: 20
baseline_policy: LOCAL_FIRST_V1
treatment_policy: SERVER_FIRST_DETERMINISTIC_V1
policy_version: v1
automatic_activation: false

source_contract:
  methodology_source_commit: 41204dc6
  exact_source_required_per_pair: true
  mixed_source_pairs_forbidden: true
  source_identity_fields:
    - base_head
    - worktree_fp
    - contract_fp
    - task_spec_fp
    - environment_fp
    - tool_contract_fp
    - evaluation_schema_fp
    - runtime_version
    - cache_stratum

analysis:
  script: resources/coding-tools-mcp/scripts/compare_route_policies.py
  analysis_script_sha256: ac53d0aaaac783253f9ea66d0dca993412097d9a3d25ff26b596a3102101103d
  population_basis: explicit_representative_comparable_pairs_status_independent
  intention_to_treat: true
  survivor_filter: false
  ttar_condition: both_actions_accepted

eligibility:
  provenance: representative
  portable_environment: true
  no_gui_affinity: true
  no_device_affinity: true
  no_secret_affinity: true
  exact_source_required: true
  strong_explicit_oracle_required: true
  deterministic_or_read_only_validation_required: true
  safe_local_fallback_required: true

primary_metrics:
  - accepted
  - first_pass
  - repair
  - TTAR

secondary_metrics:
  - queue_ms
  - transfer_ms
  - execution_ms
  - proof_ms
  - local_cpu_minutes
  - local_heavy_minutes
  - remote_compute_minutes
  - fallback
  - placement_regret_when_comparable

quality_floor:
  same_oracle_between_pair_arms: true
  same_proof_policy_between_pair_arms: true
  same_risk_policy_between_pair_arms: true
  critical_security_regression_tolerated: false
  critical_defect_regression_tolerated: false
  unresolved_authority_or_source_identity_failure_tolerated: false

assignment:
  unit: one_task_assignment_one_replicate
  pairing_required: true
  same_task_semantics: true
  same_source_snapshot: true
  same_oracle: true
  same_controller_class: true
  same_tool_contract: true
  same_environment_requirements: true
  same_risk_policy: true
  vary_only: compute_placement
  preserve_all_assigned_terminal_outcomes: true
  terminal_outcomes_in_itt:
    - accepted
    - failed
    - blocked
    - aborted
    - capacity_failed
    - activation_failed

order_randomization:
  enabled: true
  allowed_orders:
    - AB
    - BA
  record_order_index: true

cache_policy:
  explicit_stratum_required: true
  allowed_strata:
    - cold
    - warm
  cross_stratum_pairing_forbidden: true

missing_data_policy:
  missing_is_unknown_not_zero: true
  controller_token_missingness_preserved: true
  controller_monetary_cost_missingness_preserved: true
  provider_cost_requires_measurement_and_attribution: true
  incomplete_cost_forbids_CAR_claim: true
  incomplete_cost_does_not_block_instrumentation_pilot: true
  missing_cost_must_not_exclude_assigned_run_from_ITT: true
  missing_host_span_must_be_reported_not_imputed: true

promotion_gate:
  pilot_may_auto_promote: false
  pilot_pairs_are_confirmatory_proof: false
  confirmatory_cohort_required_for_broad_promotion: true
  quality_noninferiority_required_before_efficiency_claim: true
  total_cost_complete_required_for_CAR_or_cost_promotion_claim: true
  automatic_model_routing_during_P3: false
  automatic_global_server_first_during_P3: false

stop_rule:
  stop_pair_on_source_identity_mismatch: true
  stop_pair_on_task_or_oracle_identity_mismatch: true
  stop_pair_on_environment_or_cache_stratum_mismatch: true
  stop_on_analysis_script_hash_drift: true
  stop_on_critical_defect_or_security_regression: true
  stop_on_unsafe_or_unavailable_local_fallback: true
  stop_on_unresolved_authority_or_write_lease_violation: true
  do_not_replace_failed_assignment_with_successful_survivor: true
```

## 3. Intention-to-treat semantics

Every explicitly assigned representative comparable arm stays in the primary denominator regardless of terminal status. A failed, blocked or aborted server-first arm cannot disappear from the study merely because it did not reach acceptance.

Repair is defined from durable EOCL trajectory evidence. A run with at least one actual wave whose durable status is `replanned` is a repaired trajectory even if a later wave terminates `aborted`. Therefore an assigned candidate with `replanned -> aborted` contributes:

```text
candidate_acceptance = 0
candidate_first_pass = 0
candidate_repair     = 1
```

TTAR comparison is conditional on both pair arms reaching accepted state; this conditional latency analysis does not change the status-independent ITT denominator used for acceptance, first-pass and repair outcomes.

## 4. Cost and economics boundary

Controller token and monetary-cost telemetry are currently incomplete. This is missing data, not zero cost.

The pilot may proceed because its primary purpose is instrumentation and causal placement evidence for acceptance, first-pass, repair, TTAR and local burden. However:

- `CAR` is `unavailable/incomplete` whenever total monetary-cost coverage is incomplete;
- no missing controller/provider cost may be imputed as zero;
- cost-incomplete assignments remain in the ITT population;
- no placement or model promotion may be justified by a cost claim until the required measured/attributed cost coverage exists.

## 5. Representative enrollment gate

A task may be enrolled only if all of the following are true before assignment:

1. It is a real representative project task, not a synthetic/no-op task created to fill sample count.
2. Its execution/validation environment is portable.
3. It has no GUI, device or secret/local affinity that would invalidate server placement.
4. Exact source, task, environment, tool-contract and oracle identity can be recorded.
5. A strong explicit acceptance oracle exists before either arm runs.
6. A safe local fallback exists.
7. Both arms can use the same task semantics, controller class, proof policy and risk policy.
8. The only intended causal treatment difference is local-first versus server-first deterministic compute placement.

If fewer than ten genuinely eligible representative tasks are available, the pilot remains below target rather than manufacturing eligibility.

## 6. Pilot interpretation

The first 10–20 representative pairs are used only to verify instrumentation, estimate paired variance and discordance, characterize failure/capacity/fallback mix, estimate transfer/setup break-even, and power-size a confirmatory cohort.

No broad production promotion is allowed from the pilot merely because a code threshold is met. Any confirmatory study must freeze its own sample-size/power assumptions and analysis contract before outcomes are inspected.

## 7. Frozen analyzer identity

The preregistered deterministic analyzer is:

```text
resources/coding-tools-mcp/scripts/compare_route_policies.py
SHA-256 ac53d0aaaac783253f9ea66d0dca993412097d9a3d25ff26b596a3102101103d
```

Any change to this file changes the analysis identity. Existing pilot outcomes must not be silently reinterpreted under a modified analyzer; analysis drift requires an explicit new manifest/version.

## 8. Phase boundary

At freeze time:

```text
P0 source/live boundary             CLOSED
P1 measurement plumbing             PROVEN ON SYNTHETIC PAIRS
P1 ITT terminal-state semantics     CLOSED / CHECKPOINTED / DELIVERED
P1 controller economics             HOLD; MISSINGNESS PRESERVED
P2 diagnostic phase                 CLOSED / CHECKPOINTED
P2 remediation efficacy             NOT PROVEN / HOLD
P3 representative treatment         NOT YET STARTED
```

**Next allowed action after this manifest is committed/pushed:** identify genuinely eligible representative project tasks and launch the first bounded paired assignment. Pair tags alone are not evidence of server-first treatment; the execution path must demonstrate that the treatment arm actually changed compute placement.
