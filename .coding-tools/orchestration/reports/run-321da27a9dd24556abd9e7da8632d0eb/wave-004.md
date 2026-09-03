# Orchestration Wave 4

- Run: `321da27a9dd24556abd9e7da8632d0eb`
- Wave: `64c73a4c0910447385ed3b0348953ac5`
- Objective: Continue exact RUN 321da27a9dd24556abd9e7da8632d0eb only. Do not replace the RUN and do not mutate source in this prepare wave. Recapture current SHA-256 for coordination.py and test_operator_report_isolation.py, inspect the exact completion-report recovery patch/test context, and run only tests/test_operator_report_isolation.py::OperatorReportIsolationTests::test_exact_terminal_get_materializes_missing_report_without_making_audit_write once. Preserve all unrelated dirty work and do not run the prior focused group.
- Objective revision: `2`
- Objective SHA-256: `9116288c2f880091a96092733ee7c7d7c54279f25e8b801f89a2ee926f8ac59b`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `0bfdfcc495e703e0ca6f14ab181d6a5c3f8d4c863966e592bbcf94a2b1cd8fe9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35711 | 2026-09-02T09:13:35.391Z | wave_replanned |  | PREFLIGHT | reason=WAVE3 typed INVALID_ARGUMENT occurred before pytest because the Windows command path inspector treated the pytest node-id separator "::" as an invalid path. Change only the proof invocation syntax to file plus exact -k selector, which selects the same single regression and produces 1 passed with the remaining tests deselected. Do not retry the rejected node-id command. |
| 35712 | 2026-09-02T09:13:35.601Z | observation_span_recorded |  |  |  |
| 35713 | 2026-09-02T09:13:35.824Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35714 | 2026-09-02T09:13:35.998Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35715 | 2026-09-02T09:13:36.182Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 35716 | 2026-09-02T09:13:36.366Z | state_transition | READY | ROUTED | reason=route_selected |
| 35717 | 2026-09-02T09:13:36.570Z | observation_span_recorded |  |  |  |
| 35718 | 2026-09-02T09:13:37.593Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8e49c9d085ad48d39d4eb4f08e3076ba |
| 35719 | 2026-09-02T09:13:37.797Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35720 | 2026-09-02T09:13:38.766Z | existing_file_adoption_observed |  |  |  |
| 35721 | 2026-09-02T09:13:39.013Z | observation_span_recorded |  |  |  |
| 35722 | 2026-09-02T09:13:39.398Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8e49c9d085ad48d39d4eb4f08e3076ba |
| 35723 | 2026-09-02T09:13:39.574Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35724 | 2026-09-02T09:13:40.594Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:205a9c5f7702557c; input_fingerprint=6347df1c4a612afdbc0830b9202104f21182600e3270b9d2944fc284ad76d006 |
| 35725 | 2026-09-02T09:13:40.992Z | managed_process_admitted |  |  | owner=default |
| 35726 | 2026-09-02T09:13:41.342Z | managed_process_started |  |  | owner=default |
| 35727 | 2026-09-02T09:13:44.059Z | managed_process_terminal |  |  | owner=default |
| 35728 | 2026-09-02T09:13:44.474Z | proof_recorded |  |  | stage_id=check:205a9c5f7702557c; status=passed; cache_hit=False; input_fingerprint=6347df1c4a612afdbc0830b9202104f21182600e3270b9d2944fc284ad76d006 |
| 35729 | 2026-09-02T09:13:44.685Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f35155855769ab62fc17f681a0a2aa6040b1975d1297f4fc3d51a8d2d0dd70b8 |
| 35730 | 2026-09-02T09:13:45.124Z | managed_process_admitted |  |  | owner=default |
| 35731 | 2026-09-02T09:13:45.491Z | managed_process_started |  |  | owner=default |
| 35732 | 2026-09-02T09:13:59.582Z | managed_process_terminal |  |  | owner=default |
| 35733 | 2026-09-02T09:14:00.749Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f35155855769ab62fc17f681a0a2aa6040b1975d1297f4fc3d51a8d2d0dd70b8 |
| 35734 | 2026-09-02T09:14:01.022Z | observation_span_recorded |  |  |  |
| 35735 | 2026-09-02T09:14:01.249Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 35740 | 2026-09-02T09:20:54.173Z | quality_outcome_recorded |  |  |  |
| 35741 | 2026-09-02T09:20:54.389Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 35742 | 2026-09-02T09:20:54.684Z | observation_span_recorded |  |  |  |
| 35743 | 2026-09-02T09:20:54.937Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:205a9c5f7702557c | passed | 6347df1c4a612afdbc0830b9202104f21182600e3270b9d2944fc284ad76d006 | False | 3481 | 0 |
| verify:tests | passed | f35155855769ab62fc17f681a0a2aa6040b1975d1297f4fc3d51a8d2d0dd70b8 | False | 15641 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c7fdfe2cd803436a89d61bfcd52ee6db | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 2b76bf6a3b320754f2b7199216c1ec4bfe45051036d7efd4bffd5a6ede37f434 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `121`
- Chain head: `52d90336699b29d7d2db7adb7fc40c3bf8c6f9992ba059451aa77b025af1a376`
