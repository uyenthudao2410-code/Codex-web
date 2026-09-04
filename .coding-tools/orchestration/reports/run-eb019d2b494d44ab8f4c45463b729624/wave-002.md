# Orchestration Wave 2

- Run: `eb019d2b494d44ab8f4c45463b729624`
- Wave: `8695a45b43304d9d850993f9188ca3cd`
- Objective: G6 Session A: exact Problem binding, guard-compliant read-only check, and one durable identity command
- Objective revision: `2`
- Objective SHA-256: `ec69fc4a1ca28e98e6f1d511890adcd8e2778f2a064ec0797f5e2c2a1b6703b2`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `bb871a9aff0da667fefdd2d4a5659eabe781bcad12a4372de259171d5f706ae6`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39479 | 2026-09-04T07:28:21.109Z | wave_replanned |  | PREFLIGHT | reason=INVALID_ARGUMENT |
| 39480 | 2026-09-04T07:28:21.387Z | observation_span_recorded |  |  |  |
| 39481 | 2026-09-04T07:28:21.697Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39482 | 2026-09-04T07:28:21.922Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39483 | 2026-09-04T07:28:22.116Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 39484 | 2026-09-04T07:28:22.332Z | state_transition | READY | ROUTED | reason=route_selected |
| 39485 | 2026-09-04T07:28:22.603Z | observation_span_recorded |  |  |  |
| 39486 | 2026-09-04T07:28:23.722Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0b6b1419f45a4bbd8a59ffc087c5c399 |
| 39487 | 2026-09-04T07:28:23.941Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39488 | 2026-09-04T07:28:25.059Z | observation_span_recorded |  |  |  |
| 39489 | 2026-09-04T07:28:25.412Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0b6b1419f45a4bbd8a59ffc087c5c399 |
| 39490 | 2026-09-04T07:28:25.602Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39491 | 2026-09-04T07:28:27.063Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6cc35fc6a84aee2f; input_fingerprint=518feaf56b0417959e055a849a9ba3e2373f5949c99837b63422c39cfacf3c66 |
| 39492 | 2026-09-04T07:28:27.775Z | managed_process_admitted |  |  | owner=default |
| 39493 | 2026-09-04T07:28:28.146Z | managed_process_started |  |  | owner=default |
| 39494 | 2026-09-04T07:28:28.808Z | managed_process_terminal |  |  | owner=default |
| 39495 | 2026-09-04T07:28:29.231Z | proof_recorded |  |  | stage_id=check:6cc35fc6a84aee2f; status=failed; cache_hit=False; input_fingerprint=518feaf56b0417959e055a849a9ba3e2373f5949c99837b63422c39cfacf3c66 |
| 39496 | 2026-09-04T07:28:29.499Z | observation_span_recorded |  |  |  |
| 39497 | 2026-09-04T07:28:29.749Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 39498 | 2026-09-04T07:28:29.952Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 39499 | 2026-09-04T07:28:30.217Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6cc35fc6a84aee2f | failed | 518feaf56b0417959e055a849a9ba3e2373f5949c99837b63422c39cfacf3c66 | False | 1704 | 128 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `afff9058ce46280d31c6c2c6076f246ac2bc5124eb87bdd159d7a88783fbd6c1`
