# Orchestration Wave 2

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Wave: `7b30871d5c9349418e8c7f80ec0d7083`
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
| 12839 | 2026-08-17T08:53:05.544Z | wave_replanned |  | PREFLIGHT | reason=Only volatile .coding-tools orchestration/runtime evidence changed after preflight because prior acceptance/checkpoint events were persisted. Git source HEAD remains acaa3582052ab6836ade7b55bd1ff2178ebc5117 and no source/artifact boundary changed. Create a fresh read-only coherence wave fenced to the current evidence snapshot. |
| 12840 | 2026-08-17T08:53:06.004Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12841 | 2026-08-17T08:53:06.217Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12842 | 2026-08-17T08:53:06.400Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12843 | 2026-08-17T08:53:06.621Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12844 | 2026-08-17T08:53:06.818Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12845 | 2026-08-17T08:53:07.025Z | state_transition | READY | ROUTED | reason=route_selected |
| 12846 | 2026-08-17T08:53:07.540Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=193645a3b4664dd5b280e6f5336b9747 |
| 12847 | 2026-08-17T08:53:07.768Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12848 | 2026-08-17T08:53:08.236Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=193645a3b4664dd5b280e6f5336b9747 |
| 12849 | 2026-08-17T08:53:08.491Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12850 | 2026-08-17T08:53:08.898Z | proof_cache_miss |  |  | reason=cold; stage_id=check:dca69ba30efcf6ca; input_fingerprint=5b5687cd73e9c6ce7bb93ef4db3ed6de3b2ca2fab54b838b292f9523bdaedb80 |
| 12851 | 2026-08-17T08:53:09.200Z | managed_process_admitted |  |  | owner=default |
| 12852 | 2026-08-17T08:53:09.553Z | managed_process_started |  |  | owner=default |
| 12853 | 2026-08-17T08:53:11.322Z | managed_process_terminal |  |  | owner=default |
| 12854 | 2026-08-17T08:53:11.669Z | proof_recorded |  |  | stage_id=check:dca69ba30efcf6ca; status=failed; cache_hit=False; input_fingerprint=5b5687cd73e9c6ce7bb93ef4db3ed6de3b2ca2fab54b838b292f9523bdaedb80 |
| 12855 | 2026-08-17T08:53:11.927Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12856 | 2026-08-17T08:53:12.100Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12857 | 2026-08-17T08:53:12.289Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:dca69ba30efcf6ca | failed | 5b5687cd73e9c6ce7bb93ef4db3ed6de3b2ca2fab54b838b292f9523bdaedb80 | False | 2450 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`
