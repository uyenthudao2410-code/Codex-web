# Orchestration Wave 1

- Run: `a4c94733cdb841ba871c19d4e6b6a5ac`
- Wave: `7a61cde218d74cb0b7028aa85c5637b0`
- Objective: Resolve the token-measurement bug end-to-end without overwriting unrelated dirty work. Confirm current implementations of dashboard time-series bucketing, daChartTimeMode, rolling_5m semantics, controllerUsage canonical ingress, and the ChatWeb/Electron host path that should emit exact controller usage. Identify which existing dirty hunks in renderer/dashboard.js and tests/dashboard-analytics.test.js belong to prior accepted work versus this new bug. Finish line: a coherent patch making the chart honor the selected dashboard range, hourly/daily mode functional, rolling_5m remain exact last-5-minute canonical events with explicit empty-state/no fallback, and exact ChatWeb/controller usage emitted into the existing ingress when provider-reported/client-reported exact controller usage exists, with focused regression tests and no fabricated counts when usage is absent. Inspect active EOCL/task state and create or reuse a legal run/wave for this new genuine bugfix rather than colliding with another writer.
- Mode: `mcp_only`
- Base HEAD: `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02`
- Worktree fingerprint: `c37fd2a3d8add0ab374c94b7ec41704a40f1ef24294b67663fb76bf82e3f0655`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21766 | 2026-08-19T11:47:12.254Z | run_started |  | PREFLIGHT |  |
| 21767 | 2026-08-19T11:47:13.365Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21768 | 2026-08-19T11:48:17.296Z | managed_process_admitted |  |  | owner=chatweb |
| 21769 | 2026-08-19T11:48:17.568Z | managed_process_started |  |  | owner=chatweb |
| 21770 | 2026-08-19T11:48:18.039Z | managed_process_terminal |  |  | owner=chatweb |
| 21771 | 2026-08-19T11:48:31.606Z | managed_process_admitted |  |  | owner=chatweb |
| 21772 | 2026-08-19T11:48:31.846Z | managed_process_started |  |  | owner=chatweb |
| 21773 | 2026-08-19T11:48:32.305Z | managed_process_terminal |  |  | owner=chatweb |
| 21774 | 2026-08-19T11:48:40.443Z | managed_process_admitted |  |  | owner=chatweb |
| 21775 | 2026-08-19T11:48:40.730Z | managed_process_started |  |  | owner=chatweb |
| 21776 | 2026-08-19T11:48:41.122Z | managed_process_terminal |  |  | owner=chatweb |
| 21777 | 2026-08-19T11:48:48.466Z | managed_process_admitted |  |  | owner=chatweb |
| 21778 | 2026-08-19T11:48:48.777Z | managed_process_started |  |  | owner=chatweb |
| 21779 | 2026-08-19T11:48:49.254Z | managed_process_terminal |  |  | owner=chatweb |
| 21780 | 2026-08-19T11:48:58.494Z | managed_process_admitted |  |  | owner=chatweb |
| 21781 | 2026-08-19T11:48:58.764Z | managed_process_started |  |  | owner=chatweb |
| 21782 | 2026-08-19T11:48:59.139Z | managed_process_terminal |  |  | owner=chatweb |
| 21783 | 2026-08-19T11:49:08.149Z | managed_process_admitted |  |  | owner=chatweb |
| 21784 | 2026-08-19T11:49:08.391Z | managed_process_started |  |  | owner=chatweb |
| 21785 | 2026-08-19T11:49:09.071Z | managed_process_terminal |  |  | owner=chatweb |
| 21786 | 2026-08-19T11:49:17.239Z | managed_process_admitted |  |  | owner=chatweb |
| 21787 | 2026-08-19T11:49:17.474Z | managed_process_started |  |  | owner=chatweb |
| 21788 | 2026-08-19T11:49:17.887Z | managed_process_terminal |  |  | owner=chatweb |
| 21789 | 2026-08-19T11:49:28.463Z | managed_process_admitted |  |  | owner=chatweb |
| 21790 | 2026-08-19T11:49:28.694Z | managed_process_started |  |  | owner=chatweb |
| 21791 | 2026-08-19T11:49:29.137Z | managed_process_terminal |  |  | owner=chatweb |
| 21792 | 2026-08-19T11:49:37.494Z | managed_process_admitted |  |  | owner=chatweb |
| 21793 | 2026-08-19T11:49:37.773Z | managed_process_started |  |  | owner=chatweb |
| 21794 | 2026-08-19T11:49:38.232Z | managed_process_terminal |  |  | owner=chatweb |
| 21795 | 2026-08-19T11:50:46.329Z | solution_shadow_recommended |  |  |  |
| 21796 | 2026-08-19T11:50:54.558Z | managed_process_admitted |  |  | owner=chatweb |
| 21797 | 2026-08-19T11:50:54.841Z | managed_process_started |  |  | owner=chatweb |
| 21798 | 2026-08-19T11:50:55.444Z | managed_process_terminal |  |  | owner=chatweb |
| 21799 | 2026-08-19T11:51:01.680Z | managed_process_admitted |  |  | owner=chatweb |
| 21800 | 2026-08-19T11:51:01.915Z | managed_process_started |  |  | owner=chatweb |
| 21801 | 2026-08-19T11:51:02.386Z | managed_process_terminal |  |  | owner=chatweb |
| 21802 | 2026-08-19T11:51:12.163Z | managed_process_admitted |  |  | owner=chatweb |
| 21803 | 2026-08-19T11:51:12.397Z | managed_process_started |  |  | owner=chatweb |
| 21804 | 2026-08-19T11:51:12.829Z | managed_process_terminal |  |  | owner=chatweb |
| 21805 | 2026-08-19T11:51:21.508Z | managed_process_admitted |  |  | owner=chatweb |
| 21806 | 2026-08-19T11:51:21.791Z | managed_process_started |  |  | owner=chatweb |
| 21807 | 2026-08-19T11:51:22.201Z | managed_process_terminal |  |  | owner=chatweb |
| 21808 | 2026-08-19T11:51:28.980Z | managed_process_admitted |  |  | owner=chatweb |
| 21809 | 2026-08-19T11:51:29.180Z | managed_process_started |  |  | owner=chatweb |
| 21810 | 2026-08-19T11:51:29.550Z | managed_process_terminal |  |  | owner=chatweb |
| 21811 | 2026-08-19T11:51:36.007Z | managed_process_admitted |  |  | owner=chatweb |
| 21812 | 2026-08-19T11:51:36.262Z | managed_process_started |  |  | owner=chatweb |
| 21813 | 2026-08-19T11:51:36.654Z | managed_process_terminal |  |  | owner=chatweb |
| 21814 | 2026-08-19T11:52:27.869Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 21815 | 2026-08-19T11:52:28.059Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21816 | 2026-08-19T11:52:28.192Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21817 | 2026-08-19T11:52:28.365Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21818 | 2026-08-19T11:52:28.534Z | state_transition | READY | ROUTED | reason=route_selected |
| 21819 | 2026-08-19T11:52:29.032Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6a944fa1ec4f4c2d9ba0fe511f21c5ab |
| 21820 | 2026-08-19T11:52:29.205Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21821 | 2026-08-19T11:52:29.667Z | patch_surface_observed |  |  |  |
| 21822 | 2026-08-19T11:52:29.897Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6a944fa1ec4f4c2d9ba0fe511f21c5ab |
| 21823 | 2026-08-19T11:52:30.097Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21824 | 2026-08-19T11:52:30.501Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a4cf0983aca16eee; input_fingerprint=74ac2a728bdbb689eff6c7d3ac0b67c8c69849c81198a36e5028a4598e612521 |
| 21825 | 2026-08-19T11:52:30.821Z | managed_process_admitted |  |  | owner=default |
| 21826 | 2026-08-19T11:52:31.074Z | managed_process_started |  |  | owner=default |
| 21827 | 2026-08-19T11:52:31.470Z | managed_process_terminal |  |  | owner=default |
| 21828 | 2026-08-19T11:52:31.779Z | proof_recorded |  |  | stage_id=check:a4cf0983aca16eee; status=passed; cache_hit=False; input_fingerprint=74ac2a728bdbb689eff6c7d3ac0b67c8c69849c81198a36e5028a4598e612521 |
| 21829 | 2026-08-19T11:52:31.948Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5b02ceb4744043707ebb3a8992491b3ff0b207bd13c5275184dacccfd89b275d |
| 21830 | 2026-08-19T11:52:32.274Z | managed_process_admitted |  |  | owner=default |
| 21831 | 2026-08-19T11:52:32.608Z | managed_process_started |  |  | owner=default |
| 21832 | 2026-08-19T11:52:33.121Z | managed_process_terminal |  |  | owner=default |
| 21833 | 2026-08-19T11:52:33.391Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5b02ceb4744043707ebb3a8992491b3ff0b207bd13c5275184dacccfd89b275d |
| 21834 | 2026-08-19T11:52:33.828Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21835 | 2026-08-19T11:52:48.954Z | managed_process_admitted |  |  | owner=chatweb |
| 21836 | 2026-08-19T11:52:49.230Z | managed_process_started |  |  | owner=chatweb |
| 21837 | 2026-08-19T11:53:06.304Z | managed_process_terminal |  |  | owner=chatweb |
| 21838 | 2026-08-19T11:53:47.571Z | quality_outcome_recorded |  |  |  |
| 21839 | 2026-08-19T11:53:47.723Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21840 | 2026-08-19T11:53:48.070Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a4cf0983aca16eee | passed | 74ac2a728bdbb689eff6c7d3ac0b67c8c69849c81198a36e5028a4598e612521 | False | 936 | 0 |
| verify:tests | passed | 5b02ceb4744043707ebb3a8992491b3ff0b207bd13c5275184dacccfd89b275d | False | 1139 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 269bcacbcc3c44fc9522bd479a2ffac2 | accepted | 17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02 | 6464fd8215a4aa69e327a41ffb6e06303ae782bd32a25e105362b5a86d36bded | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `75`
- Chain head: `67269f0812bfcb356845f27ffe5944611f9582a8c723023227cc4b49420d0332`
