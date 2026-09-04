# Orchestration Wave 1

- Run: `922d3d323a83404897daf81819b3601a`
- Wave: `2ffd78f37c8c456b914b70eb35bdc114`
- Objective: Provenance-only adoption and exact-source proof for BASELINE ROLL-FORWARD RECOVERY. Do not change file contents. Ownership/lease exactly resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py at SHA-256 3f7e9889c21758c80490a4c6e7216a1b6e9d467d55c8d775a6a38c7ff58b9de2. Run all specified proofs. No restart/refresh, commit, push, release, deploy, or TG1-TG12 work.
- Objective revision: `1`
- Objective SHA-256: `65e8a88dea9612c3ee4eb71feb3e0b6b09dd385b7f4371728b852c0c41b37401`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `08031548f27ba4382af7e685a5e0ccf22b8096ea745e8c15e3824b1857b14fc5`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34743 | 2026-09-01T16:47:27.087Z | run_started |  | PREFLIGHT |  |
| 34744 | 2026-09-01T16:47:27.435Z | observation_span_recorded |  |  |  |
| 34745 | 2026-09-01T16:47:27.653Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34746 | 2026-09-01T16:47:27.854Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34747 | 2026-09-01T16:47:28.066Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 34748 | 2026-09-01T16:47:28.297Z | state_transition | READY | ROUTED | reason=route_selected |
| 34749 | 2026-09-01T16:47:28.543Z | observation_span_recorded |  |  |  |
| 34750 | 2026-09-01T16:47:29.497Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f06d43b1e5e144aea7fc08de2512c712 |
| 34751 | 2026-09-01T16:47:29.680Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34752 | 2026-09-01T16:47:30.395Z | existing_file_adoption_observed |  |  |  |
| 34753 | 2026-09-01T16:47:30.654Z | observation_span_recorded |  |  |  |
| 34754 | 2026-09-01T16:47:31.038Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f06d43b1e5e144aea7fc08de2512c712 |
| 34755 | 2026-09-01T16:47:31.287Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34756 | 2026-09-01T16:47:32.085Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b8b2ca0805408b75; input_fingerprint=755aa31a273c7ba7699b481ea179b686cb5dfccebe5d27c42d4db671042e68ab |
| 34757 | 2026-09-01T16:47:32.480Z | managed_process_admitted |  |  | owner=default |
| 34758 | 2026-09-01T16:47:32.793Z | managed_process_started |  |  | owner=default |
| 34759 | 2026-09-01T16:47:43.802Z | managed_process_terminal |  |  | owner=default |
| 34760 | 2026-09-01T16:47:44.256Z | proof_recorded |  |  | stage_id=check:b8b2ca0805408b75; status=passed; cache_hit=False; input_fingerprint=755aa31a273c7ba7699b481ea179b686cb5dfccebe5d27c42d4db671042e68ab |
| 34761 | 2026-09-01T16:47:44.467Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:60a11fb0bb201c3b; input_fingerprint=3b647044905c65ed4fe23a9bd198cd1e23ce6f5dd958bfc7b11cdc319bc28853 |
| 34762 | 2026-09-01T16:47:44.955Z | managed_process_admitted |  |  | owner=default |
| 34763 | 2026-09-01T16:47:45.336Z | managed_process_started |  |  | owner=default |
| 34764 | 2026-09-01T16:53:17.991Z | managed_process_terminal |  |  | owner=default |
| 34765 | 2026-09-01T16:53:18.369Z | proof_recorded |  |  | stage_id=check:60a11fb0bb201c3b; status=failed; cache_hit=False; input_fingerprint=3b647044905c65ed4fe23a9bd198cd1e23ce6f5dd958bfc7b11cdc319bc28853 |
| 34766 | 2026-09-01T16:53:18.582Z | observation_span_recorded |  |  |  |
| 34767 | 2026-09-01T16:53:18.869Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 34768 | 2026-09-01T16:53:19.086Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 34769 | 2026-09-01T16:53:19.301Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 38810 | 2026-09-03T20:02:59.821Z | state_transition | REPLAN | ABORTED | reason=G3_RECONCILE_REPLAN_ABANDONED_AFTER_CURRENT_REPORT_ACK |
| 38811 | 2026-09-03T20:03:00.281Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b8b2ca0805408b75 | passed | 755aa31a273c7ba7699b481ea179b686cb5dfccebe5d27c42d4db671042e68ab | False | 11768 | 0 |
| check:60a11fb0bb201c3b | failed | 3b647044905c65ed4fe23a9bd198cd1e23ce6f5dd958bfc7b11cdc319bc28853 | False | 333478 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `c7e68fb3c8c90a9beacd6235587a6578e53e358463c34d9f1a7b89f6b0672273`
