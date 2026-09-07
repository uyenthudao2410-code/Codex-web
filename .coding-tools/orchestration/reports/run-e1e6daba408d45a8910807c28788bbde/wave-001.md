# Orchestration Wave 1

- Run: `e1e6daba408d45a8910807c28788bbde`
- Wave: `b238a73e81d84a6f87caff7f2094f358`
- Objective: Read only the exact FullCleanActivation component-mutation path that invokes RuntimeOrchestrator for coding_mcp, especially option propagation through handoff/replay. Confirm whether a new host-side option can reach activateCodingMcpUpdate after Recovery Host replacement. Do not modify source, Git, ledger, runtime, or services.
- Objective revision: `1`
- Objective SHA-256: `6c6c12f6df1035026dd385db19d97aebf47104d0dc9b4a511912ec72734ae942`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `5825c852f3d8f5e1702c94e41d43b8ada014c93ce0e670b899d407a54257e3fe`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42881 | 2026-09-07T02:48:23.488Z | run_started |  | PREFLIGHT |  |
| 42882 | 2026-09-07T02:48:23.894Z | observation_span_recorded |  |  |  |
| 42883 | 2026-09-07T02:48:24.395Z | observation_span_recorded |  |  |  |
| 42884 | 2026-09-07T02:48:24.582Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42885 | 2026-09-07T02:48:24.787Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42886 | 2026-09-07T02:48:24.993Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42887 | 2026-09-07T02:48:25.146Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42888 | 2026-09-07T02:48:25.303Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42889 | 2026-09-07T02:48:25.455Z | state_transition | READY | ROUTED | reason=route_selected |
| 42890 | 2026-09-07T02:48:25.636Z | observation_span_recorded |  |  |  |
| 42891 | 2026-09-07T02:48:26.090Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=29a3823a306d4db9bf6d9c7a60ad0581 |
| 42892 | 2026-09-07T02:48:26.234Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42893 | 2026-09-07T02:48:26.608Z | observation_span_recorded |  |  |  |
| 42894 | 2026-09-07T02:48:26.874Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=29a3823a306d4db9bf6d9c7a60ad0581 |
| 42895 | 2026-09-07T02:48:27.018Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42896 | 2026-09-07T02:48:27.378Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4d602843f92d932f; input_fingerprint=d9e8c90f8060b16dceaf39fa7b6f15412127362814c9bbf49d811d2b64fa75b4 |
| 42897 | 2026-09-07T02:48:27.700Z | managed_process_admitted |  |  | owner=default |
| 42898 | 2026-09-07T02:48:27.921Z | managed_process_started |  |  | owner=default |
| 42899 | 2026-09-07T02:48:28.273Z | managed_process_terminal |  |  | owner=default |
| 42900 | 2026-09-07T02:48:28.565Z | proof_recorded |  |  | stage_id=check:4d602843f92d932f; status=passed; cache_hit=False; input_fingerprint=d9e8c90f8060b16dceaf39fa7b6f15412127362814c9bbf49d811d2b64fa75b4 |
| 42901 | 2026-09-07T02:48:28.738Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9248b30c8271eb24; input_fingerprint=3fd26261b29b6273dbfc16d235b6fda2f98ac1ef8876ab321208df090cbca89f |
| 42902 | 2026-09-07T02:48:29.067Z | managed_process_admitted |  |  | owner=default |
| 42903 | 2026-09-07T02:48:29.315Z | managed_process_started |  |  | owner=default |
| 42904 | 2026-09-07T02:48:29.749Z | managed_process_terminal |  |  | owner=default |
| 42905 | 2026-09-07T02:48:30.154Z | proof_recorded |  |  | stage_id=check:9248b30c8271eb24; status=passed; cache_hit=False; input_fingerprint=3fd26261b29b6273dbfc16d235b6fda2f98ac1ef8876ab321208df090cbca89f |
| 42906 | 2026-09-07T02:48:30.408Z | observation_span_recorded |  |  |  |
| 42907 | 2026-09-07T02:48:30.611Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42908 | 2026-09-07T02:49:02.386Z | quality_outcome_recorded |  |  |  |
| 42909 | 2026-09-07T02:49:02.556Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42910 | 2026-09-07T02:49:02.863Z | observation_span_recorded |  |  |  |
| 42911 | 2026-09-07T02:49:03.012Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4d602843f92d932f | passed | d9e8c90f8060b16dceaf39fa7b6f15412127362814c9bbf49d811d2b64fa75b4 | False | 912 | 0 |
| check:9248b30c8271eb24 | passed | 3fd26261b29b6273dbfc16d235b6fda2f98ac1ef8876ab321208df090cbca89f | False | 1002 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 48462c08a0ca4d3fbae5bd9188258005 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 3e3f070fe043fb805ed3d74b8a5f1d68b76b4014e35fe71b9dd77827231ff8ea | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `66710d13b9a1257f534bff7aaf0c56df3d331478a14b183982dfe234cef30e7e`
