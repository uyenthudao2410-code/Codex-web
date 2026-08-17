# Orchestration Run Summary

- Run: `053be0d4a4874400a076b26bb3ceac72`
- Task: `3013554d46344a778c2107a93609481f`
- Objective: Implement Python-side compute-first measurement hardening only, preserving all unrelated staged/unstaged changes exactly. Do NOT modify docs/PRODUCTION_CLOSURE_ROLLOUT.md, resources/recovery-supervisor, tests/recovery-supervisor.test.js, installer/Recovery/activation/release surfaces, or external system state. In resources/coding-tools-mcp: (1) bump evaluation schema version and add explicit experiment_kind separating model_routing from compute_placement while keeping backward-compatible model_routing semantics for historical rows; include experiment_kind in causal pair identity/fingerprint and prevent cross-domain pairing. (2) Add task_control action=controller_observation with a durable cumulative content-free controller snapshot contract: source, optional clock_domain, started_at/ended_at informational timestamps, same-clock duration_ms, explicitly measured pre_mcp_ms, cumulative monetary_cost and token counters. Validate cumulative counters/cost/durations never decrease; unknown remains unknown, never synthesize zero. accepted_result_evaluation must merge delayed observations over run-creation controller metadata and must NOT derive pre_mcp_ms by subtracting controller/server wall timestamps across clock domains. (3) Add task_control action=placement with a durable content-free compute placement observation: source, policy local_only/server_preferred, policy_version, source_mode, resource_class, actual_placement local/remote, reason_code, dispatch_attempted, dispatch_succeeded, fallback, selected_runner_id/tool_name/job_id optional. accepted_result_evaluation returns latest placement. For experiment_kind=compute_placement, pairing_eligible requires actual placement evidence and policy match. (4) Strengthen paired evaluation quality floor: accepted + explicit oracle_pass=true + known zero critical defects, and fail for regression_escape/rollback_required/manual_fix_required/maintainability_gate=fail when present. Compute Pareto relation only when both pair rows pass quality and accepted-result TTAR plus total monetary cost are complete; do not use weighted scores. Expose routing_regret only for model_routing and placement_regret only through a dedicated paired_compute_placement_evaluation wrapper with baseline local_only vs candidate server_preferred; tradeoffs/insufficient evidence remain indeterminate. automatic_activation must remain false. (5) Add focused tests for delayed cumulative controller observations, monotonicity rejection, cross-clock pre_mcp semantics, experiment isolation, compute-placement evidence requirement, explicit quality floor, Pareto dominance/regret/tradeoff, task_control handlers/schema, and preservation of synthetic/benchmark exclusion. Do not change public top-level tool count.
- Status: **accepted**
- Started: `2026-08-17T08:29:26.108Z`
- Finished: `2026-08-17T08:40:16.213Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `adbd58a364124a8f8d0ef3cb0d432cf1` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e45e225f8f2845c28b6fb071d82019a7 | adbd58a364124a8f8d0ef3cb0d432cf1 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | dc6129ed3187918223add8878fd723fc5cbd0daf85f1fcc7b50aec97e48adc79 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12618 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `305f2042513c3c5e1773a83eea16032d6cb3a2cd223c41204e06ad4390552f9a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
