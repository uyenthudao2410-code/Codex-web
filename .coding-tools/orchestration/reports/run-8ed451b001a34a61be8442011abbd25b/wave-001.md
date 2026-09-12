# Orchestration Wave 1

- Run: `8ed451b001a34a61be8442011abbd25b`
- Wave: `9718a0058baa409982ba59556ca0dd6b`
- Objective: Natural #16 attempt #2: implement only the P2-local typed request/control-shape causal mapping for INVALID_ARGUMENT and MODE_ROUTE_MISMATCH, preserving global economics helper semantics and all generic failure classes as unknown.
- Objective revision: `1`
- Objective SHA-256: `d93b8ab3d6839ae15c2751e883af1088658c418e20f79b911c4c544681521580`
- Objective source: `run_initial_objective`
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
| 46785 | 2026-09-10T06:24:58.724Z | run_started |  | PREFLIGHT |  |
| 46786 | 2026-09-10T06:24:59.251Z | observation_span_recorded |  |  |  |
| 46787 | 2026-09-10T06:25:05.171Z | observation_span_recorded |  |  |  |
| 46788 | 2026-09-10T06:25:05.367Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 46789 | 2026-09-10T06:25:33.052Z | solution_shadow_recommended |  |  |  |
| 46790 | 2026-09-10T06:25:33.256Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 46791 | 2026-09-10T06:25:33.450Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 46792 | 2026-09-10T06:25:33.632Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 46793 | 2026-09-10T06:25:33.829Z | state_transition | READY | ROUTED | reason=route_selected |
| 46794 | 2026-09-10T06:25:34.029Z | observation_span_recorded |  |  |  |
| 46795 | 2026-09-10T06:25:34.950Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e44d1ed5cc25468197a1027d1084f3ac |
| 46796 | 2026-09-10T06:25:35.092Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 46797 | 2026-09-10T06:25:35.869Z | patch_surface_observed |  |  |  |
| 46798 | 2026-09-10T06:25:36.020Z | observation_span_recorded |  |  |  |
| 46799 | 2026-09-10T06:25:36.290Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e44d1ed5cc25468197a1027d1084f3ac |
| 46800 | 2026-09-10T06:25:36.424Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 46801 | 2026-09-10T06:25:37.142Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ed7873ee22bf15b5; input_fingerprint=0c0c31191e03be0b01cdba1c888768b3c5e4488836673ff085d60016f25e6f92 |
| 46802 | 2026-09-10T06:25:37.560Z | managed_process_admitted |  |  | owner=default |
| 46803 | 2026-09-10T06:25:37.920Z | managed_process_started |  |  | owner=default |
| 46804 | 2026-09-10T06:25:41.679Z | managed_process_terminal |  |  | owner=default |
| 46805 | 2026-09-10T06:25:41.959Z | proof_recorded |  |  | stage_id=check:ed7873ee22bf15b5; status=passed; cache_hit=False; input_fingerprint=0c0c31191e03be0b01cdba1c888768b3c5e4488836673ff085d60016f25e6f92 |
| 46806 | 2026-09-10T06:25:42.118Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1e606d62e02d0f68; input_fingerprint=f783e81601f7cb1a441ec6065d9ebe633c7c412f5710e9205e03d529fb38a922 |
| 46807 | 2026-09-10T06:25:42.435Z | managed_process_admitted |  |  | owner=default |
| 46808 | 2026-09-10T06:25:42.745Z | managed_process_started |  |  | owner=default |
| 46809 | 2026-09-10T06:25:59.594Z | managed_process_terminal |  |  | owner=default |
| 46810 | 2026-09-10T06:26:00.020Z | proof_recorded |  |  | stage_id=check:1e606d62e02d0f68; status=passed; cache_hit=False; input_fingerprint=f783e81601f7cb1a441ec6065d9ebe633c7c412f5710e9205e03d529fb38a922 |
| 46811 | 2026-09-10T06:26:00.198Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6d884becdef27c18; input_fingerprint=5eaa037cba1da99540c9cee336dad3c7f91e6178bd2618db5fddb611f8b33145 |
| 46812 | 2026-09-10T06:26:00.560Z | managed_process_admitted |  |  | owner=default |
| 46813 | 2026-09-10T06:26:00.861Z | managed_process_started |  |  | owner=default |
| 46814 | 2026-09-10T06:26:03.753Z | managed_process_terminal |  |  | owner=default |
| 46815 | 2026-09-10T06:26:04.074Z | proof_recorded |  |  | stage_id=check:6d884becdef27c18; status=passed; cache_hit=False; input_fingerprint=5eaa037cba1da99540c9cee336dad3c7f91e6178bd2618db5fddb611f8b33145 |
| 46816 | 2026-09-10T06:26:04.259Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:20af4e8e69d7c88b; input_fingerprint=a51cf85974c1acf1f73b958755eb4e6a46d9c550f85fa97fbf54dbec93f18913 |
| 46817 | 2026-09-10T06:26:04.585Z | managed_process_admitted |  |  | owner=default |
| 46818 | 2026-09-10T06:26:04.921Z | managed_process_started |  |  | owner=default |
| 46819 | 2026-09-10T06:26:05.238Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 46820 | 2026-09-10T06:26:05.638Z | proof_recorded |  |  | stage_id=check:20af4e8e69d7c88b; status=passed; cache_hit=False; input_fingerprint=a51cf85974c1acf1f73b958755eb4e6a46d9c550f85fa97fbf54dbec93f18913 |
| 46821 | 2026-09-10T06:26:06.521Z | observation_span_recorded |  |  |  |
| 46822 | 2026-09-10T06:26:06.700Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 46823 | 2026-09-10T06:27:49.677Z | managed_process_admitted |  |  | owner=chatweb |
| 46824 | 2026-09-10T06:27:49.995Z | managed_process_started |  |  | owner=chatweb |
| 46825 | 2026-09-10T06:27:51.493Z | managed_process_terminal |  |  | owner=chatweb |
| 46826 | 2026-09-10T06:28:04.461Z | managed_process_admitted |  |  | owner=chatweb |
| 46827 | 2026-09-10T06:28:04.785Z | managed_process_started |  |  | owner=chatweb |
| 46828 | 2026-09-10T06:28:06.578Z | managed_process_terminal |  |  | owner=chatweb |
| 46829 | 2026-09-10T06:28:34.302Z | quality_outcome_recorded |  |  |  |
| 46830 | 2026-09-10T06:28:34.763Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 46831 | 2026-09-10T06:28:35.077Z | observation_span_recorded |  |  |  |
| 46832 | 2026-09-10T06:28:35.269Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ed7873ee22bf15b5 | passed | 0c0c31191e03be0b01cdba1c888768b3c5e4488836673ff085d60016f25e6f92 | False | 4514 | 0 |
| check:1e606d62e02d0f68 | passed | f783e81601f7cb1a441ec6065d9ebe633c7c412f5710e9205e03d529fb38a922 | False | 17616 | 0 |
| check:6d884becdef27c18 | passed | 5eaa037cba1da99540c9cee336dad3c7f91e6178bd2618db5fddb611f8b33145 | False | 3544 | 0 |
| check:20af4e8e69d7c88b | passed | a51cf85974c1acf1f73b958755eb4e6a46d9c550f85fa97fbf54dbec93f18913 | False | 825 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 63892f609c134f61a4d7234005ade0bd | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | b2adf95186617fb39016e55870488171d6aaa788368653ee683d9decda983b24 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `73cb5284becb26dca21cdd522d41a60d47f39d8cf91eb0f3af1e960f9fa669c9`
