# Orchestration Wave 1

- Run: `5e7544aa62bb43a4b9ea25c4f0671acb`
- Wave: `dbba59bcc81446b38c51dadcbd36f2de`
- Objective: Preflight exactly the six currently reported unresolved stale orchestration RUN IDs using the repository-supported read-only exact-ID maintenance CLI. Capture immutable snapshot/logical hashes and blocker classifications only. Do not reconcile, do not pass runtime-stopped, do not modify source/Git/ledger except ordinary current RUN evidence, and do not inspect any other historical RUN.
- Objective revision: `1`
- Objective SHA-256: `38c7a4112d68fc383ae6c4420a66cc6357b668a505e297b775117fee5f263da2`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `1f8ce07b6442346931cfcd2610c20047b7c341224ac9a059f7e79152adc73886`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42613 | 2026-09-07T02:30:52.485Z | run_started |  | PREFLIGHT |  |
| 42614 | 2026-09-07T02:30:52.849Z | observation_span_recorded |  |  |  |
| 42615 | 2026-09-07T02:30:53.292Z | observation_span_recorded |  |  |  |
| 42616 | 2026-09-07T02:30:53.525Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42617 | 2026-09-07T02:30:53.674Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42618 | 2026-09-07T02:30:53.855Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42619 | 2026-09-07T02:30:54.038Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42620 | 2026-09-07T02:30:54.205Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42621 | 2026-09-07T02:30:54.417Z | state_transition | READY | ROUTED | reason=route_selected |
| 42622 | 2026-09-07T02:30:54.599Z | observation_span_recorded |  |  |  |
| 42623 | 2026-09-07T02:30:55.025Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3e07d91e7a4b4964b96d8f31246405f1 |
| 42624 | 2026-09-07T02:30:55.217Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42625 | 2026-09-07T02:30:55.599Z | observation_span_recorded |  |  |  |
| 42626 | 2026-09-07T02:30:55.885Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3e07d91e7a4b4964b96d8f31246405f1 |
| 42627 | 2026-09-07T02:30:56.076Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42628 | 2026-09-07T02:30:56.501Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b74350fe4eb9fccf; input_fingerprint=fe5e5acf24f9e6a427b3391c281286fafa63b7314c811af7637fa706fac9ae04 |
| 42629 | 2026-09-07T02:30:56.877Z | managed_process_admitted |  |  | owner=default |
| 42630 | 2026-09-07T02:30:57.171Z | managed_process_started |  |  | owner=default |
| 42631 | 2026-09-07T02:30:57.630Z | managed_process_terminal |  |  | owner=default |
| 42632 | 2026-09-07T02:30:57.949Z | proof_recorded |  |  | stage_id=check:b74350fe4eb9fccf; status=failed; cache_hit=False; input_fingerprint=fe5e5acf24f9e6a427b3391c281286fafa63b7314c811af7637fa706fac9ae04 |
| 42633 | 2026-09-07T02:30:58.165Z | observation_span_recorded |  |  |  |
| 42634 | 2026-09-07T02:30:58.360Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42635 | 2026-09-07T02:30:58.536Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42636 | 2026-09-07T02:30:58.736Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b74350fe4eb9fccf | failed | fe5e5acf24f9e6a427b3391c281286fafa63b7314c811af7637fa706fac9ae04 | False | 1134 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `74`
- Chain head: `675c0f0af65252c437cd3e7955b11cc12bed2eb4fd0915cd07645de3ff109f9c`
