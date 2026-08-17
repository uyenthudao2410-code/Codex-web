# Orchestration Wave 3

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Wave: `b528b4bd2ced4fefa171b976d9c13321`
- Objective: Finish the remaining compute-first/server-first measurement and evaluation hardening on the isolated worktree only. Preserve current routing authority and production Recovery/installer behavior. Diagnose current code first and identify the smallest coherent implementation that makes local-first versus server-first compute placement genuinely measurable without fake tags: (1) keep compute placement distinct from model-route evaluation, (2) provide an enforceable study-only placement choice or equivalent exact policy identity so a run tagged local-first cannot silently execute server-first and vice versa, without changing the default server-first production policy, (3) persist content-free actual placement decision/execution/fallback evidence with reason/provenance and exact source/environment identity, (4) support delayed controller economics and quality/observation correlation using existing ledger/task_control contracts rather than inventing duplicate telemetry, (5) add a fail-closed paired compute-placement evaluator with quality floor, TTA/total-cost completeness, Pareto/regret projection, representative-only evidence, and automatic_activation=false, (6) preserve unknown cost as unknown, exclude benchmark/synthetic/fault/recovery acceptance rows, and do not claim counterfactual regret from a single run, (7) keep host turn/run/wave binding intact, (8) correct any runtime telemetry field that falsely says shadow-only if live dispatch is actually enabled, but only if current contract evidence proves it is semantically wrong. Add focused tests and update maintained current-state/measurement documentation only if public/operational behavior changes. Do not touch resources/recovery-supervisor, Recovery tests, installer/package surfaces, external Windows state, or main checkout. Do not commit, push, tag, release, restart runtime, or edit volatile .coding-tools evidence. Worktree: .git/compute-placement-evaluation, branch automation/compute-placement-evaluation-20260817, expected base acaa3582052ab6836ade7b55bd1ff2178ebc5117.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12858 | 2026-08-17T08:53:38.663Z | wave_replanned |  | PREFLIGHT | reason=The anonymous coherence probe reached the primary control endpoint but correctly received Unauthorized. This changes the verification strategy: inspect the source-defined local control authentication contract and then use the credential internally without exposing it, rather than retrying the same anonymous request. |
| 12859 | 2026-08-17T08:53:39.281Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12860 | 2026-08-17T08:53:39.487Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12861 | 2026-08-17T08:53:39.691Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12862 | 2026-08-17T08:53:39.891Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12863 | 2026-08-17T08:53:40.115Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12864 | 2026-08-17T08:53:40.275Z | state_transition | READY | ROUTED | reason=route_selected |
| 12865 | 2026-08-17T08:53:40.831Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0e4a61d299e249efa20588ce4bd228d0 |
| 12866 | 2026-08-17T08:53:40.995Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12867 | 2026-08-17T08:53:41.192Z | failure_observed | EXECUTING | EXECUTING | failure_class=INVALID_ARGUMENT |
| 12868 | 2026-08-17T08:53:41.480Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=0e4a61d299e249efa20588ce4bd228d0 |
| 12869 | 2026-08-17T08:53:41.648Z | state_transition | EXECUTING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 12870 | 2026-08-17T08:53:41.898Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`
