# Orchestration Wave 1

- Run: `9e932500096b4860b8a1e39a2da56b3e`
- Wave: `8531475220934fdfbbcc01ff948fbc56`
- Objective: G2-P14 provenance closure ONLY for exact current usage history/accounting packet. Adopt without changing source bytes exactly resources/coding-tools-mcp/coding_tools_mcp/usage_ledger.py SHA-256 14c58c27b0f84bf69c2de68c8554d38eb0a010d7f31953331c2076d44d893262; resources/coding-tools-mcp/coding_tools_mcp/usage_pricing.py SHA-256 7521b595a952d2bed229ef9ec904864e7545bf94f49b2775331aad8187b48327; resources/coding-tools-mcp/tests/test_usage_accounting_v2.py SHA-256 9a1498d06d07e9b47cf2ca68123336c72ddf8da64af1a56ab9621a7b6e129ee6; resources/coding-tools-mcp/tests/test_usage_history_w9.py SHA-256 55c294ac068f03f3728034a4867993ac0d6fe0cc68ce1a4efa7b9b52a3b53577. Causal objective: canonical longitudinal UsageEvent history is append-only/exact-only; controller usage dedupes across waves without replacing provider identity; historical backfill accepts exact events only; queries use bounded stable keyset pages and stable usage IDs; coverage is time-aware; pricing revision is explicit; missing measurements remain unknown_not_zero; no plausible estimates or overlap double-counting. Preserve dirty worktree and all .coding-tools evidence. No source outside these four paths; no direct SQLite; no stale-RUN reconciliation; no bulk adoption; no synthetic Problems/outcomes/cohorts; no reset/restore/clean/rebase; no secrets; no commit/push/tag/release/publish/deploy.
- Objective revision: `1`
- Objective SHA-256: `cb532a62ede923043c16c1f42ba5adcb56cb9b8894619a24ff76e07a6b9c344c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38500 | 2026-09-03T18:17:04.748Z | run_started |  | PREFLIGHT |  |
| 38501 | 2026-09-03T18:17:05.193Z | observation_span_recorded |  |  |  |
| 38502 | 2026-09-03T18:17:06.153Z | observation_span_recorded |  |  |  |
| 38503 | 2026-09-03T18:17:06.404Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38504 | 2026-09-03T18:17:06.616Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38505 | 2026-09-03T18:17:06.817Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38506 | 2026-09-03T18:17:06.988Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38507 | 2026-09-03T18:17:07.223Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38508 | 2026-09-03T18:17:07.427Z | state_transition | READY | ROUTED | reason=route_selected |
| 38509 | 2026-09-03T18:17:07.648Z | observation_span_recorded |  |  |  |
| 38510 | 2026-09-03T18:17:08.689Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=128239ebe0f54c87ae5cda4d4e10795f |
| 38511 | 2026-09-03T18:17:08.877Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38512 | 2026-09-03T18:17:09.832Z | existing_file_adoption_observed |  |  |  |
| 38513 | 2026-09-03T18:17:10.036Z | observation_span_recorded |  |  |  |
| 38514 | 2026-09-03T18:17:10.331Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=128239ebe0f54c87ae5cda4d4e10795f |
| 38515 | 2026-09-03T18:17:10.473Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38516 | 2026-09-03T18:17:11.307Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ae3fa99bfcb6ddff; input_fingerprint=16e92abe7700462030f745a28594f07a5d406c5093409d3acb08ffecfb27dadb |
| 38517 | 2026-09-03T18:17:11.700Z | managed_process_admitted |  |  | owner=default |
| 38518 | 2026-09-03T18:17:12.174Z | managed_process_started |  |  | owner=default |
| 38519 | 2026-09-03T18:17:12.701Z | managed_process_terminal |  |  | owner=default |
| 38520 | 2026-09-03T18:17:13.188Z | proof_recorded |  |  | stage_id=check:ae3fa99bfcb6ddff; status=passed; cache_hit=False; input_fingerprint=16e92abe7700462030f745a28594f07a5d406c5093409d3acb08ffecfb27dadb |
| 38521 | 2026-09-03T18:17:13.366Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3a0fdb1b99c0d051; input_fingerprint=98688dba27bcfb72686a9325ad5e0152243c32d548c23c88e7e3ac40561aee36 |
| 38522 | 2026-09-03T18:17:13.764Z | managed_process_admitted |  |  | owner=default |
| 38523 | 2026-09-03T18:17:14.065Z | managed_process_started |  |  | owner=default |
| 38524 | 2026-09-03T18:17:21.317Z | managed_process_terminal |  |  | owner=default |
| 38525 | 2026-09-03T18:17:21.781Z | proof_recorded |  |  | stage_id=check:3a0fdb1b99c0d051; status=passed; cache_hit=False; input_fingerprint=98688dba27bcfb72686a9325ad5e0152243c32d548c23c88e7e3ac40561aee36 |
| 38526 | 2026-09-03T18:17:22.025Z | observation_span_recorded |  |  |  |
| 38527 | 2026-09-03T18:17:22.251Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38528 | 2026-09-03T18:18:27.582Z | quality_outcome_recorded |  |  |  |
| 38529 | 2026-09-03T18:18:27.791Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38530 | 2026-09-03T18:18:28.116Z | observation_span_recorded |  |  |  |
| 38531 | 2026-09-03T18:18:28.380Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ae3fa99bfcb6ddff | passed | 16e92abe7700462030f745a28594f07a5d406c5093409d3acb08ffecfb27dadb | False | 1436 | 0 |
| check:3a0fdb1b99c0d051 | passed | 98688dba27bcfb72686a9325ad5e0152243c32d548c23c88e7e3ac40561aee36 | False | 7996 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 21f0f9669ab64002bc4db2a4e8a78891 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 685d16e5856c3560724fabe44542adebd0aa9972839bba42797d39e26d0261a1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `99263b03be85de0037a6fbf31134b5ab028b20b77d0dbcb3da081fa4ddf947c6`
