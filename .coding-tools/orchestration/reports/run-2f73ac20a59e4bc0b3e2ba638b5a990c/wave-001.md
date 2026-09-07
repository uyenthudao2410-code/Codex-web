# Orchestration Wave 1

- Run: `2f73ac20a59e4bc0b3e2ba638b5a990c`
- Wave: `372b9ae942c14d54bed96108f117d49a`
- Objective: Start the local WebCodex native semantic provider for E:\DEV\Codex-web from the repaired machine state at C:\Users\Admin\AppData\Local\WebCodex\g4-semantic\codex-web-current, then verify a webcodex process remains alive. Do not modify repository source, Git, ledger, activation configuration, or release artifacts.
- Objective revision: `1`
- Objective SHA-256: `759c0324b4d6c7728a9ab078a6443e5b6d4996d03c7ba0b28c59ec12277bebfb`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `5c7c04dbe08093df17462094e6fcbd44e29f691345f347af639325d7305f7b85`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42378 | 2026-09-07T02:17:29.176Z | run_started |  | PREFLIGHT |  |
| 42379 | 2026-09-07T02:17:29.531Z | observation_span_recorded |  |  |  |
| 42380 | 2026-09-07T02:17:30.028Z | observation_span_recorded |  |  |  |
| 42381 | 2026-09-07T02:17:30.230Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42382 | 2026-09-07T02:17:30.470Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42383 | 2026-09-07T02:17:30.676Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42384 | 2026-09-07T02:17:30.908Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42385 | 2026-09-07T02:17:31.093Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42386 | 2026-09-07T02:17:31.275Z | state_transition | READY | ROUTED | reason=route_selected |
| 42387 | 2026-09-07T02:17:31.459Z | observation_span_recorded |  |  |  |
| 42388 | 2026-09-07T02:17:31.933Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=37d08655f15d4048b6a5b053cb62ea10 |
| 42389 | 2026-09-07T02:17:32.135Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42390 | 2026-09-07T02:17:32.514Z | observation_span_recorded |  |  |  |
| 42391 | 2026-09-07T02:17:32.833Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=37d08655f15d4048b6a5b053cb62ea10 |
| 42392 | 2026-09-07T02:17:33.053Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42393 | 2026-09-07T02:17:33.415Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ed926dea0a25a588; input_fingerprint=09b43aa869a75b5ab06bf4e9cc1e9c8055a00810c6cd0b8b935b3465c0c927e7 |
| 42394 | 2026-09-07T02:17:33.847Z | managed_process_admitted |  |  | owner=default |
| 42395 | 2026-09-07T02:17:34.189Z | managed_process_started |  |  | owner=default |
| 42396 | 2026-09-07T02:17:34.689Z | managed_process_terminal |  |  | owner=default |
| 42397 | 2026-09-07T02:17:35.058Z | proof_recorded |  |  | stage_id=check:ed926dea0a25a588; status=passed; cache_hit=False; input_fingerprint=09b43aa869a75b5ab06bf4e9cc1e9c8055a00810c6cd0b8b935b3465c0c927e7 |
| 42398 | 2026-09-07T02:17:35.274Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c099fa841443430b; input_fingerprint=40978f7becd6fcd7c7a5409bb5b01338f7113ba2864640d4fe8f38a2154ae19a |
| 42399 | 2026-09-07T02:17:35.709Z | managed_process_admitted |  |  | owner=default |
| 42400 | 2026-09-07T02:17:36.071Z | managed_process_started |  |  | owner=default |
| 42401 | 2026-09-07T02:17:38.668Z | managed_process_terminal |  |  | owner=default |
| 42402 | 2026-09-07T02:17:38.996Z | proof_recorded |  |  | stage_id=check:c099fa841443430b; status=failed; cache_hit=False; input_fingerprint=40978f7becd6fcd7c7a5409bb5b01338f7113ba2864640d4fe8f38a2154ae19a |
| 42403 | 2026-09-07T02:17:39.236Z | observation_span_recorded |  |  |  |
| 42404 | 2026-09-07T02:17:39.436Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42405 | 2026-09-07T02:17:39.626Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42406 | 2026-09-07T02:17:39.819Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ed926dea0a25a588 | passed | 09b43aa869a75b5ab06bf4e9cc1e9c8055a00810c6cd0b8b935b3465c0c927e7 | False | 1204 | 0 |
| check:c099fa841443430b | failed | 40978f7becd6fcd7c7a5409bb5b01338f7113ba2864640d4fe8f38a2154ae19a | False | 3354 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `139`
- Chain head: `27e07c13675e7babc01a534fac9e304ceff482c33898fdad217869a5037c5f98`
