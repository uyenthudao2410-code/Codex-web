# Orchestration Wave 4

- Run: `b8897e320dc14416a6376e3206b2a848`
- Wave: `42f885d0d6d64c5894a8932390ea0f04`
- Objective: Natural #19 Wave 4 diagnosis only: intersect the global target failures with the exact accepted representative chatweb_mcp repaired deterministic cohort used by rework_diagnosis, using the existing read-only ledger-history utility and the reporter's exact route/evaluation filters. Then identify the exact target run IDs and whether a typed permission reason is durably present. No source or ledger mutation.
- Objective revision: `4`
- Objective SHA-256: `3a9f178d6f529cfddc28d76c3b61b1c2bc649c8ef259b0ea7e8912c689424bac`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `1e78fe9b5a4abac5845c3450fee92ce4c4af2bbdd99b513742399b8c4bcef1fa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47064 | 2026-09-10T07:28:01.489Z | wave_replanned |  | PREFLIGHT | reason=Wave 3 recovered the 46-event global target set. Wave 4 changes evidence scope to the reporter's exact accepted representative repaired deterministic cohort, using read-only subqueries and exact route filters so the 13 cohort occurrences can be identified without inference. |
| 47065 | 2026-09-10T07:28:01.736Z | observation_span_recorded |  |  |  |
| 47066 | 2026-09-10T07:28:07.812Z | observation_span_recorded |  |  |  |
| 47067 | 2026-09-10T07:28:08.014Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47068 | 2026-09-10T07:29:16.393Z | managed_process_admitted |  |  | owner=default |
| 47069 | 2026-09-10T07:29:16.789Z | managed_process_started |  |  | owner=default |
| 47070 | 2026-09-10T07:29:17.322Z | managed_process_terminal |  |  | owner=default |
| 47071 | 2026-09-10T07:29:30.315Z | managed_process_admitted |  |  | owner=default |
| 47072 | 2026-09-10T07:29:30.709Z | managed_process_started |  |  | owner=default |
| 47073 | 2026-09-10T07:29:31.273Z | managed_process_terminal |  |  | owner=default |
| 47074 | 2026-09-10T07:29:45.731Z | managed_process_admitted |  |  | owner=default |
| 47075 | 2026-09-10T07:29:46.152Z | managed_process_started |  |  | owner=default |
| 47076 | 2026-09-10T07:29:46.764Z | managed_process_terminal |  |  | owner=default |
| 47077 | 2026-09-10T07:30:00.836Z | managed_process_admitted |  |  | owner=default |
| 47078 | 2026-09-10T07:30:01.171Z | managed_process_started |  |  | owner=default |
| 47079 | 2026-09-10T07:30:01.734Z | managed_process_terminal |  |  | owner=default |
| 47080 | 2026-09-10T07:30:14.403Z | managed_process_admitted |  |  | owner=default |
| 47081 | 2026-09-10T07:30:14.778Z | managed_process_started |  |  | owner=default |
| 47082 | 2026-09-10T07:30:15.345Z | managed_process_terminal |  |  | owner=default |
| 47083 | 2026-09-10T07:32:35.368Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47084 | 2026-09-10T07:32:35.541Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47085 | 2026-09-10T07:32:35.716Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 47086 | 2026-09-10T07:32:35.876Z | state_transition | READY | ROUTED | reason=route_selected |
| 47087 | 2026-09-10T07:32:36.041Z | observation_span_recorded |  |  |  |
| 47088 | 2026-09-10T07:32:37.419Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d84b49de54ad44f4b60508c6beda2904 |
| 47089 | 2026-09-10T07:32:37.634Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47090 | 2026-09-10T07:32:38.854Z | observation_span_recorded |  |  |  |
| 47091 | 2026-09-10T07:32:39.151Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d84b49de54ad44f4b60508c6beda2904 |
| 47092 | 2026-09-10T07:32:39.338Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47093 | 2026-09-10T07:32:40.437Z | proof_cache_miss |  |  | reason=cold; stage_id=check:74758a80f0782ab7; input_fingerprint=c6e281f506058c9f7c7666b932e451afb11a11ad466fe282a7ca38a8e3755fd5 |
| 47094 | 2026-09-10T07:32:40.822Z | managed_process_admitted |  |  | owner=default |
| 47095 | 2026-09-10T07:32:41.179Z | managed_process_started |  |  | owner=default |
| 47096 | 2026-09-10T07:32:41.810Z | managed_process_terminal |  |  | owner=default |
| 47097 | 2026-09-10T07:32:42.110Z | proof_recorded |  |  | stage_id=check:74758a80f0782ab7; status=passed; cache_hit=False; input_fingerprint=c6e281f506058c9f7c7666b932e451afb11a11ad466fe282a7ca38a8e3755fd5 |
| 47098 | 2026-09-10T07:32:42.297Z | observation_span_recorded |  |  |  |
| 47099 | 2026-09-10T07:32:42.496Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 47100 | 2026-09-10T07:33:26.709Z | observation_span_recorded |  |  |  |
| 47101 | 2026-09-10T07:33:26.944Z | failure_observed | ACCEPTING | ACCEPTING | reason=Wave 4 successfully identified the current canonical P2 target set: exactly 13 current-ledger events (12 PERMISSION_REQUIRED and one PROTECTED_PATH_WRITE), with archive-shard rows clearly separable by _source_file. The sole current-cohort PROTECTED_PATH_WRITE is run bcc88bbf410241bd942297c0fa5b15cc seq 34908. Diagnosis is not yet causally complete because rework_diagnosis pairs each failure_observed with sorted wave_replanned events by index; inspect those exact durable pairs for the 11 target runs before deciding whether any target can be mapped to request_contract_correction. Do not infer from class names alone.; failure_class=SOL_REJECTED |
| 47102 | 2026-09-10T07:33:27.149Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 47103 | 2026-09-10T07:33:27.339Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:74758a80f0782ab7 | passed | c6e281f506058c9f7c7666b932e451afb11a11ad466fe282a7ca38a8e3755fd5 | False | 1377 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `146`
- Chain head: `3a25b061be5f24c8d9aa63c4619f4995991feb539b8703037a9e80b721b28a34`
