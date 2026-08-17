# Orchestration Wave 4

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Wave: `1641e600a27a4e6db226516c84db3688`
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
| 12871 | 2026-08-17T08:53:53.550Z | wave_replanned |  | PREFLIGHT | reason=The anonymous coherence probe reached the primary control endpoint but correctly received Unauthorized. This changes the verification strategy: inspect the source-defined local control authentication contract and then use the credential internally without exposing it, rather than retrying the same anonymous request. |
| 12872 | 2026-08-17T08:53:53.983Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12873 | 2026-08-17T08:55:07.902Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12874 | 2026-08-17T08:55:26.893Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12875 | 2026-08-17T08:55:27.183Z | managed_process_started |  |  | owner=chatweb-compute |
| 12876 | 2026-08-17T08:55:27.626Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12877 | 2026-08-17T08:55:30.367Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12878 | 2026-08-17T08:55:36.658Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12879 | 2026-08-17T08:55:36.958Z | managed_process_started |  |  | owner=chatweb-compute |
| 12880 | 2026-08-17T08:55:37.398Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12881 | 2026-08-17T08:55:45.947Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12882 | 2026-08-17T08:55:46.291Z | managed_process_started |  |  | owner=chatweb-compute |
| 12883 | 2026-08-17T08:55:46.802Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12884 | 2026-08-17T08:55:58.975Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12885 | 2026-08-17T08:55:59.324Z | managed_process_started |  |  | owner=chatweb-compute |
| 12886 | 2026-08-17T08:55:59.782Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12887 | 2026-08-17T08:56:22.830Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12888 | 2026-08-17T08:56:23.206Z | managed_process_started |  |  | owner=chatweb-compute |
| 12889 | 2026-08-17T08:56:23.694Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12890 | 2026-08-17T08:56:31.957Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12891 | 2026-08-17T08:56:32.211Z | managed_process_started |  |  | owner=chatweb-compute |
| 12892 | 2026-08-17T08:56:32.639Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12893 | 2026-08-17T08:56:39.889Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12894 | 2026-08-17T08:56:40.169Z | managed_process_started |  |  | owner=chatweb-compute |
| 12895 | 2026-08-17T08:56:40.731Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12896 | 2026-08-17T08:56:51.173Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12897 | 2026-08-17T08:56:51.411Z | managed_process_started |  |  | owner=chatweb-compute |
| 12898 | 2026-08-17T08:56:51.838Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12899 | 2026-08-17T08:57:31.268Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12900 | 2026-08-17T08:57:31.465Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12901 | 2026-08-17T08:57:31.616Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12902 | 2026-08-17T08:57:31.764Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 12903 | 2026-08-17T08:57:31.941Z | state_transition | READY | ROUTED | reason=route_selected |
| 12904 | 2026-08-17T08:57:32.384Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ddc203f5460f4a909226995b15c16c9d |
| 12905 | 2026-08-17T08:57:32.517Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12906 | 2026-08-17T08:57:33.069Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ddc203f5460f4a909226995b15c16c9d |
| 12907 | 2026-08-17T08:57:33.276Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12908 | 2026-08-17T08:57:33.612Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ef6ccfaa94d5e103; input_fingerprint=3e74d7a46d127d5fc6bd9b51074d6b897ffff9f3857f30f4d589ec0b3f7a3d60 |
| 12909 | 2026-08-17T08:57:34.010Z | managed_process_admitted |  |  | owner=default |
| 12910 | 2026-08-17T08:57:34.342Z | managed_process_started |  |  | owner=default |
| 12911 | 2026-08-17T08:57:35.958Z | managed_process_terminal |  |  | owner=default |
| 12912 | 2026-08-17T08:57:36.246Z | proof_recorded |  |  | stage_id=check:ef6ccfaa94d5e103; status=failed; cache_hit=False; input_fingerprint=3e74d7a46d127d5fc6bd9b51074d6b897ffff9f3857f30f4d589ec0b3f7a3d60 |
| 12913 | 2026-08-17T08:57:36.399Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12914 | 2026-08-17T08:57:36.557Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12915 | 2026-08-17T08:57:36.842Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ef6ccfaa94d5e103 | failed | 3e74d7a46d127d5fc6bd9b51074d6b897ffff9f3857f30f4d589ec0b3f7a3d60 | False | 2214 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`
