# Orchestration Wave 3

- Run: `aa0d0f75ae454d74aaea036438fa9b37`
- Wave: `458402b8a4154700885a0de4214935c9`
- Objective: Terminal Wave 3 verification for the committed P5 restart/activation preflight fix. Verify only: lifecycle-only P5 anchors must not be selected by current_active_execution_run and therefore must not block restart/activation; a real active EOCL execution must still block those preflights. Do not modify source unless this fresh oracle fails because of a real regression. Preserve Codex Desktop P5 authority and all previously closed work.
- Objective revision: `3`
- Objective SHA-256: `8cf7a1664f2f0ce74a28ef73f3a24f0f79c63aa4348f8bd324f6ac6af29ced3e`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `769ad3625a5000d8911eb08ae715982a7fd4b6bd`
- Worktree fingerprint: `959b10f52577cbf6d2c5e20e6a9cdaa7e999c462e0bccc72c7dd25aa12fcf91b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26956 | 2026-08-22T08:53:49.035Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 was correctly rejected because its test oracle still mocked lifecycle-wide current_active_run. The committed tree now contains migrated mocks for current_active_execution_run plus the P5-anchor restart regression. Open a replacement wave on the same run and produce fresh proof; do not reuse Wave 2 evidence. |
| 26957 | 2026-08-22T08:53:50.269Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26958 | 2026-08-22T08:53:58.527Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 26959 | 2026-08-22T08:53:58.710Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26960 | 2026-08-22T08:53:58.869Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26961 | 2026-08-22T08:53:59.621Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 26962 | 2026-08-22T08:53:59.985Z | state_transition | READY | ROUTED | reason=route_selected |
| 26963 | 2026-08-22T08:54:00.877Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f622527b7e5c4ab1b582bf4b74d61e38 |
| 26964 | 2026-08-22T08:54:01.069Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26965 | 2026-08-22T08:54:02.036Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f622527b7e5c4ab1b582bf4b74d61e38 |
| 26966 | 2026-08-22T08:54:02.184Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26967 | 2026-08-22T08:54:03.031Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=90a11a415e5220ad41e1a5f508962824593b8238655125e26fd766fdfd5a3d46 |
| 26968 | 2026-08-22T08:54:03.459Z | managed_process_admitted |  |  | owner=default |
| 26969 | 2026-08-22T08:54:03.701Z | managed_process_started |  |  | owner=default |
| 26970 | 2026-08-22T08:54:10.794Z | managed_process_terminal |  |  | owner=default |
| 26971 | 2026-08-22T08:54:18.149Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=90a11a415e5220ad41e1a5f508962824593b8238655125e26fd766fdfd5a3d46 |
| 26972 | 2026-08-22T08:54:18.352Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26973 | 2026-08-22T08:55:33.216Z | managed_process_admitted |  |  | owner=chatweb |
| 26974 | 2026-08-22T08:55:33.518Z | managed_process_started |  |  | owner=chatweb |
| 26975 | 2026-08-22T08:55:33.938Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=chatweb |
| 26976 | 2026-08-22T08:55:43.742Z | managed_process_admitted |  |  | owner=chatweb |
| 26977 | 2026-08-22T08:55:44.023Z | managed_process_started |  |  | owner=chatweb |
| 26978 | 2026-08-22T08:55:44.513Z | managed_process_terminal |  |  | owner=chatweb |
| 26979 | 2026-08-22T08:55:58.540Z | quality_outcome_recorded |  |  |  |
| 26980 | 2026-08-22T08:55:58.706Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 26981 | 2026-08-22T08:55:59.031Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 90a11a415e5220ad41e1a5f508962824593b8238655125e26fd766fdfd5a3d46 | False | 14781 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ce32d20b0d81426e96047d2d9f7de831 | accepted | 769ad3625a5000d8911eb08ae715982a7fd4b6bd | f28766f4a4829cd9abd56d2a633b48c4a85b5232297578f845c0ee6ab9aab496 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `10c9e264fa31e523b95d7551af049bb65322da38ac9ae465e66923cc13f3290d`
