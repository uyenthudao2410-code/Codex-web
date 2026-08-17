# Orchestration Wave 6

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Wave: `bbfabb23f96d43ebb6d55e159847b0ac`
- Objective: Finish the remaining compute-first/server-first measurement and evaluation hardening on the isolated worktree only. Preserve current routing authority and production Recovery/installer behavior. Diagnose current code first and identify the smallest coherent implementation that makes local-first versus server-first compute placement genuinely measurable without fake tags: (1) keep compute placement distinct from model-route evaluation, (2) provide an enforceable study-only placement choice or equivalent exact policy identity so a run tagged local-first cannot silently execute server-first and vice versa, without changing the default server-first production policy, (3) persist content-free actual placement decision/execution/fallback evidence with reason/provenance and exact source/environment identity, (4) support delayed controller economics and quality/observation correlation using existing ledger/task_control contracts rather than inventing duplicate telemetry, (5) add a fail-closed paired compute-placement evaluator with quality floor, TTA/total-cost completeness, Pareto/regret projection, representative-only evidence, and automatic_activation=false, (6) preserve unknown cost as unknown, exclude benchmark/synthetic/fault/recovery acceptance rows, and do not claim counterfactual regret from a single run, (7) keep host turn/run/wave binding intact, (8) correct any runtime telemetry field that falsely says shadow-only if live dispatch is actually enabled, but only if current contract evidence proves it is semantically wrong. Add focused tests and update maintained current-state/measurement documentation only if public/operational behavior changes. Do not touch resources/recovery-supervisor, Recovery tests, installer/package surfaces, external Windows state, or main checkout. Do not commit, push, tag, release, restart runtime, or edit volatile .coding-tools evidence. Worktree: .git/compute-placement-evaluation, branch automation/compute-placement-evaluation-20260817, expected base acaa3582052ab6836ade7b55bd1ff2178ebc5117.
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
| 12983 | 2026-08-17T09:01:37.054Z | wave_replanned |  | PREFLIGHT | reason=The rollback mutation itself passed, and the authenticated Recovery IPC health proof after rollback also passed. Only the final PowerShell listener check failed because `$pid` conflicts case-insensitively with PowerShell's read-only automatic `$PID` variable. This wave changes only that verification variable to `$ownerPid` and explicitly does not rerun Uninstall. |
| 12984 | 2026-08-17T09:01:37.524Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12985 | 2026-08-17T09:01:37.693Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12986 | 2026-08-17T09:01:37.890Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12987 | 2026-08-17T09:01:38.029Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12988 | 2026-08-17T09:01:38.183Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12989 | 2026-08-17T09:01:38.344Z | state_transition | READY | ROUTED | reason=route_selected |
| 12990 | 2026-08-17T09:01:38.925Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=aaf8a37416df42d2855c7acd26e7a5ae |
| 12991 | 2026-08-17T09:01:39.116Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12992 | 2026-08-17T09:01:39.638Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=aaf8a37416df42d2855c7acd26e7a5ae |
| 12993 | 2026-08-17T09:01:39.817Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12994 | 2026-08-17T09:01:40.219Z | proof_cache_miss |  |  | reason=cold; stage_id=check:849b67c1361a8304; input_fingerprint=d01e331bcb9dfeee031357e6c6daa4635cbdc19f63b0fa2eeb3e5db7e4446dd2 |
| 12995 | 2026-08-17T09:01:40.607Z | managed_process_admitted |  |  | owner=default |
| 12996 | 2026-08-17T09:01:40.906Z | managed_process_started |  |  | owner=default |
| 12997 | 2026-08-17T09:01:43.547Z | managed_process_terminal |  |  | owner=default |
| 12998 | 2026-08-17T09:01:43.796Z | proof_recorded |  |  | stage_id=check:849b67c1361a8304; status=passed; cache_hit=False; input_fingerprint=d01e331bcb9dfeee031357e6c6daa4635cbdc19f63b0fa2eeb3e5db7e4446dd2 |
| 12999 | 2026-08-17T09:01:43.987Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13000 | 2026-08-17T09:01:48.353Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 13001 | 2026-08-17T09:01:48.624Z | managed_process_started |  |  | owner=chatweb-compute |
| 13002 | 2026-08-17T09:01:49.137Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 13003 | 2026-08-17T09:01:57.690Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 13004 | 2026-08-17T09:01:58.095Z | managed_process_started |  |  | owner=chatweb-compute |
| 13005 | 2026-08-17T09:02:02.336Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13006 | 2026-08-17T09:02:02.945Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 13007 | 2026-08-17T09:02:03.142Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:849b67c1361a8304 | passed | d01e331bcb9dfeee031357e6c6daa4635cbdc19f63b0fa2eeb3e5db7e4446dd2 | False | 3251 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2381e14e36c248caa363c326be61d126 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 151d06aee9c8b009f3bed55257106ef6d782183b03ad5bee80ccfff865efaf19 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`
