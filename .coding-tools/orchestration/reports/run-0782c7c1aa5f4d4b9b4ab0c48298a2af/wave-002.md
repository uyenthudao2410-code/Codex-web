# Orchestration Wave 2

- Run: `0782c7c1aa5f4d4b9b4ab0c48298a2af`
- Wave: `be83285c600a4b9dae746b12ab072906`
- Objective: Natural #15: add phase-aware P2 accepted-run timing metrics without changing total TTA or EOCL timing semantics. Aggregate durable phase_timing into engineering-active and acceptance-wait measurements, stratified by first-pass vs repaired, preserving unknown when phase timing is incomplete. Add focused regression including a first-pass accepted run dominated by ACCEPTING wait.
- Objective revision: `1`
- Objective SHA-256: `59087184a89cd315ab4ebe43d249322ecd6b205da17e02e6a9fbe636c1c3f207`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `a70ba4f5fd17eac577e4c97ffed7f22608b4a0a6f8e11f5f3a2fbac24d11d70e`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 46661 | 2026-09-10T05:25:46.231Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 source patch was applied, but the first oracle command was invoked from the repository root with a dotted module path that requires resources/coding-tools-mcp on sys.path. The failure was ModuleNotFoundError before tests ran. Wave 2 changes evidence strategy only: run the focused unittest from resources/coding-tools-mcp, preserve current source bytes, then patch only if that correct oracle exposes an implementation defect. |
| 46662 | 2026-09-10T05:25:46.432Z | observation_span_recorded |  |  |  |
| 46663 | 2026-09-10T05:25:51.985Z | observation_span_recorded |  |  |  |
| 46664 | 2026-09-10T05:25:52.180Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46665 | 2026-09-10T05:27:10.004Z | managed_process_admitted |  |  | owner=chatweb |
| 46666 | 2026-09-10T05:27:10.368Z | managed_process_started |  |  | owner=chatweb |
| 46667 | 2026-09-10T05:27:10.713Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=chatweb |
| 46668 | 2026-09-10T05:27:20.855Z | managed_process_admitted |  |  | owner=chatweb |
| 46669 | 2026-09-10T05:27:21.235Z | managed_process_started |  |  | owner=chatweb |
| 46670 | 2026-09-10T05:27:21.646Z | managed_process_terminal |  |  | owner=chatweb |
| 46671 | 2026-09-10T05:27:45.158Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46672 | 2026-09-10T05:27:45.332Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46673 | 2026-09-10T05:27:45.498Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 46674 | 2026-09-10T05:27:45.682Z | state_transition | READY | ROUTED | reason=route_selected |
| 46675 | 2026-09-10T05:27:45.855Z | observation_span_recorded |  |  |  |
| 46676 | 2026-09-10T05:27:46.719Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=46049eb08d634db68da61ee86f2acf9a |
| 46677 | 2026-09-10T05:27:46.861Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46678 | 2026-09-10T05:27:47.746Z | existing_file_adoption_observed |  |  |  |
| 46679 | 2026-09-10T05:27:47.922Z | observation_span_recorded |  |  |  |
| 46680 | 2026-09-10T05:27:48.139Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=46049eb08d634db68da61ee86f2acf9a |
| 46681 | 2026-09-10T05:27:48.482Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46682 | 2026-09-10T05:27:49.443Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3a54753b220a7b8a; input_fingerprint=8b74351897658a71e6a57df9c6dad920ea36acd02edc265399b3c374fe7162be |
| 46683 | 2026-09-10T05:27:49.800Z | managed_process_admitted |  |  | owner=default |
| 46684 | 2026-09-10T05:27:50.119Z | managed_process_started |  |  | owner=default |
| 46685 | 2026-09-10T05:27:54.780Z | managed_process_terminal |  |  | owner=default |
| 46686 | 2026-09-10T05:27:55.069Z | proof_recorded |  |  | stage_id=check:3a54753b220a7b8a; status=passed; cache_hit=False; input_fingerprint=8b74351897658a71e6a57df9c6dad920ea36acd02edc265399b3c374fe7162be |
| 46687 | 2026-09-10T05:27:55.239Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1e606d62e02d0f68; input_fingerprint=5326c2545e9469b9a06dbc4d25f01166e716f8209fac3af6fa101542fb42ec36 |
| 46688 | 2026-09-10T05:27:55.523Z | managed_process_admitted |  |  | owner=default |
| 46689 | 2026-09-10T05:27:55.822Z | managed_process_started |  |  | owner=default |
| 46690 | 2026-09-10T05:28:10.047Z | managed_process_terminal |  |  | owner=default |
| 46691 | 2026-09-10T05:28:10.375Z | proof_recorded |  |  | stage_id=check:1e606d62e02d0f68; status=passed; cache_hit=False; input_fingerprint=5326c2545e9469b9a06dbc4d25f01166e716f8209fac3af6fa101542fb42ec36 |
| 46692 | 2026-09-10T05:28:10.583Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6d884becdef27c18; input_fingerprint=bf647021758638559c3edbd7e34fc2aeac313310b9d0f914cddbdbf09f5b3d4b |
| 46693 | 2026-09-10T05:28:10.963Z | managed_process_admitted |  |  | owner=default |
| 46694 | 2026-09-10T05:28:11.288Z | managed_process_started |  |  | owner=default |
| 46695 | 2026-09-10T05:28:14.122Z | managed_process_terminal |  |  | owner=default |
| 46696 | 2026-09-10T05:28:14.490Z | proof_recorded |  |  | stage_id=check:6d884becdef27c18; status=passed; cache_hit=False; input_fingerprint=bf647021758638559c3edbd7e34fc2aeac313310b9d0f914cddbdbf09f5b3d4b |
| 46697 | 2026-09-10T05:28:14.760Z | proof_cache_miss |  |  | reason=cold; stage_id=check:20af4e8e69d7c88b; input_fingerprint=38a3bce6dd633709f5fb2712587730bc94344ac3ba314ad17c5591b5455d7fca |
| 46698 | 2026-09-10T05:28:15.126Z | managed_process_admitted |  |  | owner=default |
| 46699 | 2026-09-10T05:28:15.491Z | managed_process_started |  |  | owner=default |
| 46700 | 2026-09-10T05:28:15.955Z | managed_process_terminal |  |  | owner=default |
| 46701 | 2026-09-10T05:28:16.232Z | proof_recorded |  |  | stage_id=check:20af4e8e69d7c88b; status=passed; cache_hit=False; input_fingerprint=38a3bce6dd633709f5fb2712587730bc94344ac3ba314ad17c5591b5455d7fca |
| 46702 | 2026-09-10T05:28:16.384Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f8077893c337c0d977387221b36c082335ca82bbe8fd5434c23540a5d2c9af99 |
| 46703 | 2026-09-10T05:28:16.688Z | managed_process_admitted |  |  | owner=default |
| 46704 | 2026-09-10T05:28:16.958Z | managed_process_started |  |  | owner=default |
| 46705 | 2026-09-10T05:29:58.552Z | managed_process_terminal |  |  | owner=default |
| 46706 | 2026-09-10T05:30:05.347Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f8077893c337c0d977387221b36c082335ca82bbe8fd5434c23540a5d2c9af99 |
| 46707 | 2026-09-10T05:30:05.579Z | observation_span_recorded |  |  |  |
| 46708 | 2026-09-10T05:30:05.718Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 46709 | 2026-09-10T05:35:29.403Z | managed_process_admitted |  |  | owner=chatweb |
| 46710 | 2026-09-10T05:35:29.734Z | managed_process_started |  |  | owner=chatweb |
| 46711 | 2026-09-10T05:35:30.207Z | managed_process_terminal |  |  | owner=chatweb |
| 46712 | 2026-09-10T05:49:49.655Z | managed_process_admitted |  |  | owner=default |
| 46713 | 2026-09-10T05:49:50.260Z | managed_process_started |  |  | owner=default |
| 46714 | 2026-09-10T05:49:50.950Z | managed_process_terminal |  |  | owner=default |
| 46715 | 2026-09-10T05:51:16.480Z | managed_process_admitted |  |  | owner=default |
| 46716 | 2026-09-10T05:51:16.810Z | managed_process_started |  |  | owner=default |
| 46717 | 2026-09-10T05:51:17.235Z | managed_process_terminal |  |  | owner=default |
| 46718 | 2026-09-10T05:52:22.794Z | managed_process_admitted |  |  | owner=default |
| 46719 | 2026-09-10T05:52:23.148Z | managed_process_started |  |  | owner=default |
| 46720 | 2026-09-10T05:52:23.594Z | managed_process_terminal |  |  | owner=default |
| 46721 | 2026-09-10T05:52:37.256Z | managed_process_admitted |  |  | owner=default |
| 46722 | 2026-09-10T05:52:37.606Z | managed_process_started |  |  | owner=default |
| 46723 | 2026-09-10T05:52:38.111Z | managed_process_terminal |  |  | owner=default |
| 46724 | 2026-09-10T05:52:51.939Z | managed_process_admitted |  |  | owner=default |
| 46725 | 2026-09-10T05:52:52.269Z | managed_process_started |  |  | owner=default |
| 46726 | 2026-09-10T05:52:52.771Z | managed_process_terminal |  |  | owner=default |
| 46727 | 2026-09-10T05:53:04.581Z | managed_process_admitted |  |  | owner=default |
| 46728 | 2026-09-10T05:53:04.947Z | managed_process_started |  |  | owner=default |
| 46729 | 2026-09-10T05:53:07.091Z | managed_process_terminal |  |  | owner=default |
| 46730 | 2026-09-10T05:53:43.563Z | quality_outcome_recorded |  |  |  |
| 46731 | 2026-09-10T05:53:43.714Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 46732 | 2026-09-10T05:53:44.004Z | observation_span_recorded |  |  |  |
| 46733 | 2026-09-10T05:53:44.206Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3a54753b220a7b8a | passed | 8b74351897658a71e6a57df9c6dad920ea36acd02edc265399b3c374fe7162be | False | 5328 | 0 |
| check:1e606d62e02d0f68 | passed | 5326c2545e9469b9a06dbc4d25f01166e716f8209fac3af6fa101542fb42ec36 | False | 14843 | 0 |
| check:6d884becdef27c18 | passed | bf647021758638559c3edbd7e34fc2aeac313310b9d0f914cddbdbf09f5b3d4b | False | 3566 | 0 |
| check:20af4e8e69d7c88b | passed | 38a3bce6dd633709f5fb2712587730bc94344ac3ba314ad17c5591b5455d7fca | False | 1136 | 0 |
| verify:tests | passed | f8077893c337c0d977387221b36c082335ca82bbe8fd5434c23540a5d2c9af99 | False | 108625 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fc8f4b3a6aa64340846915ce7735e77c | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 809ec8fc70c9ea998518c3430ff1457979ccec198aae41a731ba38bb83f9759a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `113`
- Chain head: `ae4879d61ae7e90a326f395c7b00c0afb492fac98b7cf8be046beee20050e2e2`
