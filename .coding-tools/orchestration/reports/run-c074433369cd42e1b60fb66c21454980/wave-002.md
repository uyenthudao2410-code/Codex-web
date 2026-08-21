# Orchestration Wave 2

- Run: `c074433369cd42e1b60fb66c21454980`
- Wave: `69542f8ba41f40338a3d023e3ed45e97`
- Objective: S3 / W4 preflight only. Recover the smallest current implementation surface for Semantic Repository Graph MVP without mutation. Preserve smart-v3 8-tool public contract and existing semantic_localization fallback/provider-health behavior. Inspect semantic_localization.py, context_tools.py, and focused semantic tests to determine: existing provider status/binding contract; existing localization result shape and source identity; where an internal read-only graph can be added without a new authority/tool; exact minimal V1 graph API for resolve_symbols/references/related_tests/impact; stale/hash/completeness/confidence semantics; and the smallest focused tests. Do not write source/docs in this prepare wave. Do not bypass NATIVE_LSP_BINDING_NOT_CONFIGURED or credentials/origin requirements.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `46744618755f389760e35f6a5a3cbbc9f54e095396b673430c31ede4c30c3228`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24678 | 2026-08-21T00:03:35.236Z | wave_replanned |  | PREFLIGHT | reason=ChatWeb Sol rejected wave 1 after finding a deterministic false-stale bug: later large files can be initially sampled with only the remaining total byte budget, but the record stored a larger generic per-file budget for refresh. Wave 2 keeps the implementation and fixes only that exact metadata mismatch plus a regression that fails under the rejected behavior. |
| 24679 | 2026-08-21T00:03:35.418Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24680 | 2026-08-21T00:03:35.587Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24681 | 2026-08-21T00:03:35.769Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 24682 | 2026-08-21T00:03:35.952Z | state_transition | READY | ROUTED | reason=route_selected |
| 24683 | 2026-08-21T00:03:36.419Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b9cc5b7515914568820c8c5081765de8 |
| 24684 | 2026-08-21T00:03:36.569Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24685 | 2026-08-21T00:03:37.011Z | patch_surface_observed |  |  |  |
| 24686 | 2026-08-21T00:03:37.219Z | patch_surface_observed |  |  |  |
| 24687 | 2026-08-21T00:03:37.568Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b9cc5b7515914568820c8c5081765de8 |
| 24688 | 2026-08-21T00:03:37.790Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24689 | 2026-08-21T00:03:38.176Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:ae052bed87c29fdc; input_fingerprint=4d8c975b4b8cd8c6c237528f722a11eebefcb71b19da3b9a9c0cd821b34e38ac |
| 24690 | 2026-08-21T00:03:38.507Z | managed_process_admitted |  |  | owner=default |
| 24691 | 2026-08-21T00:03:38.799Z | managed_process_started |  |  | owner=default |
| 24692 | 2026-08-21T00:03:39.187Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24693 | 2026-08-21T00:03:39.556Z | proof_recorded |  |  | stage_id=check:ae052bed87c29fdc; status=passed; cache_hit=False; input_fingerprint=4d8c975b4b8cd8c6c237528f722a11eebefcb71b19da3b9a9c0cd821b34e38ac |
| 24694 | 2026-08-21T00:03:39.718Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7d7da8c2890bbbc2; input_fingerprint=173c3c0ced3bfee4731f2febd634134aad455da2397e9f7587deb31eba68fd7e |
| 24695 | 2026-08-21T00:03:40.161Z | managed_process_admitted |  |  | owner=default |
| 24696 | 2026-08-21T00:03:40.550Z | managed_process_started |  |  | owner=default |
| 24697 | 2026-08-21T00:03:41.467Z | managed_process_terminal |  |  | owner=default |
| 24698 | 2026-08-21T00:03:41.817Z | proof_recorded |  |  | stage_id=check:7d7da8c2890bbbc2; status=passed; cache_hit=False; input_fingerprint=173c3c0ced3bfee4731f2febd634134aad455da2397e9f7587deb31eba68fd7e |
| 24699 | 2026-08-21T00:03:42.269Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 24700 | 2026-08-21T00:04:09.312Z | failure_observed | ACCEPTING | ACCEPTING | reason=Second S3 acceptance review found one remaining W4 boundedness defect: max_records currently bounds each incremental update but not the lifetime in-memory graph, so repeated disjoint queries can accumulate unbounded records. Reject wave 2 and add a hard global MAX_GRAPH_RECORD_BUDGET eviction of oldest derived records plus a repeated-batch regression. The per-file identity-budget fix itself is correct and remains preserved. No other scope expansion.; failure_class=SOL_REJECTED |
| 24701 | 2026-08-21T00:04:09.451Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 24702 | 2026-08-21T00:04:09.705Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ae052bed87c29fdc | passed | 4d8c975b4b8cd8c6c237528f722a11eebefcb71b19da3b9a9c0cd821b34e38ac | False | 818 | 0 |
| check:7d7da8c2890bbbc2 | passed | 173c3c0ced3bfee4731f2febd634134aad455da2397e9f7587deb31eba68fd7e | False | 1716 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `93`
- Chain head: `293e9a9d5ee098ecb501c1144b88e696d2ca8afa4170aa8e9841a0cdd9f7d92e`
