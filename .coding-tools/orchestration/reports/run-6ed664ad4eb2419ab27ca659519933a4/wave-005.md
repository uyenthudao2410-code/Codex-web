# Orchestration Wave 5

- Run: `6ed664ad4eb2419ab27ca659519933a4`
- Wave: `3f806415a330408d9cafac264c788337`
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
| 12916 | 2026-08-17T08:57:57.363Z | wave_replanned |  | PREFLIGHT | reason=The safeStorage helper process exited 0 but produced no safe result, so its bootstrap path is not a reliable acceptance harness. Rather than retrying Electron helper startup or touching secrets directly, switch to the already-shipped authenticated Recovery Host IPC client, which is the product control plane and keeps its bearer/token internal. |
| 12917 | 2026-08-17T08:57:57.899Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12918 | 2026-08-17T08:59:08.479Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12919 | 2026-08-17T08:59:09.982Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12920 | 2026-08-17T08:59:10.332Z | managed_process_started |  |  | owner=chatweb-compute |
| 12921 | 2026-08-17T08:59:10.995Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12946 | 2026-08-17T09:00:33.591Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12947 | 2026-08-17T09:00:33.899Z | managed_process_started |  |  | owner=chatweb-compute |
| 12948 | 2026-08-17T09:00:34.458Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12949 | 2026-08-17T09:00:46.848Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12950 | 2026-08-17T09:00:47.282Z | managed_process_started |  |  | owner=chatweb-compute |
| 12951 | 2026-08-17T09:00:55.998Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 12952 | 2026-08-17T09:00:56.146Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12953 | 2026-08-17T09:00:56.456Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12954 | 2026-08-17T09:00:56.825Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12955 | 2026-08-17T09:00:56.977Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12956 | 2026-08-17T09:00:57.123Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12957 | 2026-08-17T09:00:57.305Z | state_transition | READY | ROUTED | reason=route_selected |
| 12958 | 2026-08-17T09:00:57.850Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1ae3c7066db141a0aa23c17bc35e3844 |
| 12959 | 2026-08-17T09:00:58.106Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12960 | 2026-08-17T09:00:58.667Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1ae3c7066db141a0aa23c17bc35e3844 |
| 12961 | 2026-08-17T09:00:58.914Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12962 | 2026-08-17T09:00:59.302Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e53f8beba8eaebaa; input_fingerprint=73fb86fa1ac85c225e6dab47191509ff404018bd14cbc8985b2faad80ae853d4 |
| 12963 | 2026-08-17T09:00:59.628Z | managed_process_admitted |  |  | owner=default |
| 12964 | 2026-08-17T09:00:59.931Z | managed_process_started |  |  | owner=default |
| 12965 | 2026-08-17T09:01:04.923Z | managed_process_terminal |  |  | owner=default |
| 12966 | 2026-08-17T09:01:05.326Z | proof_recorded |  |  | stage_id=check:e53f8beba8eaebaa; status=passed; cache_hit=False; input_fingerprint=73fb86fa1ac85c225e6dab47191509ff404018bd14cbc8985b2faad80ae853d4 |
| 12967 | 2026-08-17T09:01:05.611Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4dd07cc1c59dec55; input_fingerprint=8c1d056860d18a56cf5d22735d866ad6029758d31a6d65a61cc9a19926d0946b |
| 12968 | 2026-08-17T09:01:06.539Z | managed_process_admitted |  |  | owner=default |
| 12969 | 2026-08-17T09:01:07.126Z | managed_process_started |  |  | owner=default |
| 12970 | 2026-08-17T09:01:07.705Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 12971 | 2026-08-17T09:01:08.104Z | proof_recorded |  |  | stage_id=check:4dd07cc1c59dec55; status=passed; cache_hit=False; input_fingerprint=8c1d056860d18a56cf5d22735d866ad6029758d31a6d65a61cc9a19926d0946b |
| 12972 | 2026-08-17T09:01:08.256Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 12973 | 2026-08-17T09:01:08.776Z | proof_cache_miss |  |  | reason=cold; stage_id=check:00041c995205d581; input_fingerprint=6727a2d6dd6b822ed42d961073962f0d58642470df75402601a95bdd4187acda |
| 12974 | 2026-08-17T09:01:09.173Z | managed_process_started |  |  | owner=chatweb-compute |
| 12975 | 2026-08-17T09:01:09.575Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=chatweb-compute |
| 12976 | 2026-08-17T09:01:10.268Z | managed_process_admitted |  |  | owner=default |
| 12977 | 2026-08-17T09:01:10.737Z | managed_process_started |  |  | owner=default |
| 12978 | 2026-08-17T09:01:12.313Z | managed_process_terminal |  |  | owner=default |
| 12979 | 2026-08-17T09:01:12.805Z | proof_recorded |  |  | stage_id=check:00041c995205d581; status=failed; cache_hit=False; input_fingerprint=6727a2d6dd6b822ed42d961073962f0d58642470df75402601a95bdd4187acda |
| 12980 | 2026-08-17T09:01:12.997Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12981 | 2026-08-17T09:01:13.206Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12982 | 2026-08-17T09:01:13.388Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e53f8beba8eaebaa | passed | 73fb86fa1ac85c225e6dab47191509ff404018bd14cbc8985b2faad80ae853d4 | False | 5637 | 0 |
| check:4dd07cc1c59dec55 | passed | 8c1d056860d18a56cf5d22735d866ad6029758d31a6d65a61cc9a19926d0946b | False | 1795 | 0 |
| check:00041c995205d581 | failed | 6727a2d6dd6b822ed42d961073962f0d58642470df75402601a95bdd4187acda | False | 3642 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `150`
- Chain head: `3224b0dac4d9479f5a25f345201fd8f84ab55d1a4dd82aaada20f464d2f2c5f1`
