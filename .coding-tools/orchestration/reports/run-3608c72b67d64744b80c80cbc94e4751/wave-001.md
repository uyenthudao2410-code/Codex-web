# Orchestration Wave 1

- Run: `3608c72b67d64744b80c80cbc94e4751`
- Wave: `384dfca465ad4ebab278a260bd2ef1a6`
- Objective: Finish the remaining exact ChatWeb controller-token measurement work on the current authoritative workspace. First verify whether this newly connected ChatWeb/Coding MCP host is now supplying authoritative exact controller token metadata into the existing canonical ingress. Preserve fail-closed semantics: never estimate/tokenize DOM text, never convert missing measurement to zero, preserve strict rolling_5m behavior, and preserve the already-merged 7-day/hour-day dashboard behavior. If the host is still not supplying exact usage, localize the smallest repository-owned integration point that can consume an authoritative host/provider usage payload without spoofing provenance. Also determine whether the dashboard should surface analytics.controller_usage.status explicitly. Read/diagnose only in this phase; no source mutation yet.
- Mode: `mcp_only`
- Base HEAD: `eae4298c3530d4bec059b36b9dfe9d37257828b1`
- Worktree fingerprint: `2020f01330f30f5feb2c525e098df1877426856849034ed093ae81b3e5951a22`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21855 | 2026-08-19T13:29:32.981Z | run_started |  | PREFLIGHT |  |
| 21856 | 2026-08-19T13:30:13.138Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21857 | 2026-08-19T13:31:56.845Z | managed_process_admitted |  |  | owner=chatweb |
| 21858 | 2026-08-19T13:31:57.062Z | managed_process_started |  |  | owner=chatweb |
| 21859 | 2026-08-19T13:31:57.428Z | managed_process_terminal |  |  | owner=chatweb |
| 21860 | 2026-08-19T13:32:04.611Z | managed_process_admitted |  |  | owner=chatweb |
| 21861 | 2026-08-19T13:32:04.828Z | managed_process_started |  |  | owner=chatweb |
| 21862 | 2026-08-19T13:32:05.162Z | managed_process_terminal |  |  | owner=chatweb |
| 21863 | 2026-08-19T13:33:08.876Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21864 | 2026-08-19T13:33:08.977Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21865 | 2026-08-19T13:33:09.086Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21866 | 2026-08-19T13:33:09.192Z | state_transition | READY | ROUTED | reason=route_selected |
| 21867 | 2026-08-19T13:33:09.546Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ee45b7c5cb7a4b20a74b1e52495d936c |
| 21868 | 2026-08-19T13:33:09.652Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21869 | 2026-08-19T13:33:09.972Z | patch_surface_observed |  |  |  |
| 21870 | 2026-08-19T13:33:10.169Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ee45b7c5cb7a4b20a74b1e52495d936c |
| 21871 | 2026-08-19T13:33:10.269Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21872 | 2026-08-19T13:33:10.566Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a4cf0983aca16eee; input_fingerprint=c16afa75b14bf5cb60e0456c725b9cb30534794ab7d59748b415b1108f61fbb9 |
| 21873 | 2026-08-19T13:33:10.823Z | managed_process_admitted |  |  | owner=default |
| 21874 | 2026-08-19T13:33:11.036Z | managed_process_started |  |  | owner=default |
| 21875 | 2026-08-19T13:33:11.352Z | managed_process_terminal |  |  | owner=default |
| 21876 | 2026-08-19T13:33:11.562Z | proof_recorded |  |  | stage_id=check:a4cf0983aca16eee; status=passed; cache_hit=False; input_fingerprint=c16afa75b14bf5cb60e0456c725b9cb30534794ab7d59748b415b1108f61fbb9 |
| 21877 | 2026-08-19T13:33:11.672Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d52c16a37b7f448f; input_fingerprint=b26e212aa1e5acdc27cbc3744a25df14c733eb00cb0d4001b327d89ee562c361 |
| 21878 | 2026-08-19T13:33:11.919Z | managed_process_admitted |  |  | owner=default |
| 21879 | 2026-08-19T13:33:12.127Z | managed_process_started |  |  | owner=default |
| 21880 | 2026-08-19T13:33:12.443Z | managed_process_terminal |  |  | owner=default |
| 21881 | 2026-08-19T13:33:12.678Z | proof_recorded |  |  | stage_id=check:d52c16a37b7f448f; status=passed; cache_hit=False; input_fingerprint=b26e212aa1e5acdc27cbc3744a25df14c733eb00cb0d4001b327d89ee562c361 |
| 21882 | 2026-08-19T13:33:12.795Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=59dd94d21e4f9dec2e238511a970b0c3517e637cc9b5b1b9a4f25d49458beb70 |
| 21883 | 2026-08-19T13:33:13.043Z | managed_process_admitted |  |  | owner=default |
| 21884 | 2026-08-19T13:33:13.276Z | managed_process_started |  |  | owner=default |
| 21885 | 2026-08-19T13:33:13.619Z | managed_process_terminal |  |  | owner=default |
| 21886 | 2026-08-19T13:33:20.862Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=59dd94d21e4f9dec2e238511a970b0c3517e637cc9b5b1b9a4f25d49458beb70 |
| 21887 | 2026-08-19T13:33:21.342Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21888 | 2026-08-19T13:35:18.768Z | quality_outcome_recorded |  |  |  |
| 21889 | 2026-08-19T13:35:18.908Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21890 | 2026-08-19T13:35:19.205Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a4cf0983aca16eee | passed | c16afa75b14bf5cb60e0456c725b9cb30534794ab7d59748b415b1108f61fbb9 | False | 769 | 0 |
| check:d52c16a37b7f448f | passed | b26e212aa1e5acdc27cbc3744a25df14c733eb00cb0d4001b327d89ee562c361 | False | 751 | 0 |
| verify:tests | passed | 59dd94d21e4f9dec2e238511a970b0c3517e637cc9b5b1b9a4f25d49458beb70 | False | 7719 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2d24a93fd7ce4a568802618ff29b2415 | accepted | eae4298c3530d4bec059b36b9dfe9d37257828b1 | 643104f2dc229a886451c0f213000b33786b85891aa25fc809f570651d1096e0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `878e94083bb5f940c22a04aea1e540a78724d4f22133bfa0c94d96fbaa87131b`
