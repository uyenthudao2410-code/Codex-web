# Orchestration Wave 1

- Run: `f211467f7bc34e58945da71d58a12f92`
- Wave: `efe5370263c644a28266a1a8fec93e30`
- Objective: G2-P2 provenance closure only for the exact current untracked usage reservation packet. Adopt, without changing source bytes, exactly resources/coding-tools-mcp/coding_tools_mcp/usage_reservations.py at SHA-256 8f0f9abfa28d623303bc15ea0412054f6421b9f62f9edddeec5d9f87c4734f1e and resources/coding-tools-mcp/tests/test_usage_reservations.py at SHA-256 02dd380ecb49f021eea7065eb0d07e1124ca53140b2a2b2ecb854db62744dc74. Prove the reservation lifecycle is durable on the canonical event ledger: estimates never become actual usage; absent exact usage remains indeterminate/unobserved rather than zero; reserve/reconcile are idempotent; conflicting or expired authority fails closed; late exact reconciliation is valid; abort is terminal for dispatch. provider_runtime.py, server.py, and test_execution_hub.py are ACCEPTED_CURRENT context only and must not be adopted or modified. Preserve all concurrent WIP and all paths outside this two-file scope. No bulk adoption, direct SQLite access/mutation, fake outcome/cohort data, process/lease manipulation, reconcile of stale runs, restart, reset, restore, clean, rebase, commit, push, tag, release, publish, or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Objective revision: `1`
- Objective SHA-256: `a37d907fa25830654fa8be368ebd23739d78535766fbb8c876ee6a58ef0f4028`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6e9a91755453f579b1b44200b78043fb1794a60c0b9770d93484d0c428df5dd2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37873 | 2026-09-03T16:31:12.020Z | run_started |  | PREFLIGHT |  |
| 37875 | 2026-09-03T16:31:12.650Z | observation_span_recorded |  |  |  |
| 37876 | 2026-09-03T16:31:13.477Z | observation_span_recorded |  |  |  |
| 37877 | 2026-09-03T16:31:13.692Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37878 | 2026-09-03T16:31:14.167Z | managed_process_admitted |  |  | owner=default |
| 37879 | 2026-09-03T16:31:14.532Z | managed_process_started |  |  | owner=default |
| 37880 | 2026-09-03T16:31:16.908Z | managed_process_terminal |  |  | owner=default |
| 37881 | 2026-09-03T16:31:17.144Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 37882 | 2026-09-03T16:31:17.317Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37883 | 2026-09-03T16:31:17.573Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37884 | 2026-09-03T16:31:17.728Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 37885 | 2026-09-03T16:31:17.916Z | state_transition | READY | ROUTED | reason=route_selected |
| 37886 | 2026-09-03T16:31:18.142Z | observation_span_recorded |  |  |  |
| 37887 | 2026-09-03T16:31:19.190Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3fa390e67eb64787933e40143ec3a310 |
| 37888 | 2026-09-03T16:31:19.419Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37889 | 2026-09-03T16:31:20.433Z | existing_file_adoption_observed |  |  |  |
| 37890 | 2026-09-03T16:31:20.658Z | observation_span_recorded |  |  |  |
| 37891 | 2026-09-03T16:31:21.075Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3fa390e67eb64787933e40143ec3a310 |
| 37892 | 2026-09-03T16:31:21.303Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37893 | 2026-09-03T16:31:22.255Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0093b92a450e4e35; input_fingerprint=e75f429e02a8d5b0dd7843e113934a708590eda09a3280496a44234f0097c082 |
| 37894 | 2026-09-03T16:31:22.700Z | managed_process_admitted |  |  | owner=default |
| 37895 | 2026-09-03T16:31:23.100Z | managed_process_started |  |  | owner=default |
| 37896 | 2026-09-03T16:31:23.617Z | managed_process_terminal |  |  | owner=default |
| 37897 | 2026-09-03T16:31:24.063Z | proof_recorded |  |  | stage_id=check:0093b92a450e4e35; status=passed; cache_hit=False; input_fingerprint=e75f429e02a8d5b0dd7843e113934a708590eda09a3280496a44234f0097c082 |
| 37898 | 2026-09-03T16:31:24.296Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=36aaf62e2f41613d3f0a2d78f35835f50706eb89439ba327cdefa0632258a1b9 |
| 37899 | 2026-09-03T16:31:24.750Z | managed_process_admitted |  |  | owner=default |
| 37900 | 2026-09-03T16:31:25.159Z | managed_process_started |  |  | owner=default |
| 37901 | 2026-09-03T16:31:26.417Z | managed_process_terminal |  |  | owner=default |
| 37902 | 2026-09-03T16:31:27.582Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=36aaf62e2f41613d3f0a2d78f35835f50706eb89439ba327cdefa0632258a1b9 |
| 37903 | 2026-09-03T16:31:27.813Z | observation_span_recorded |  |  |  |
| 37904 | 2026-09-03T16:31:28.092Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37912 | 2026-09-03T16:32:26.660Z | quality_outcome_recorded |  |  |  |
| 37913 | 2026-09-03T16:32:26.865Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 37914 | 2026-09-03T16:32:27.156Z | observation_span_recorded |  |  |  |
| 37915 | 2026-09-03T16:32:27.413Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:0093b92a450e4e35 | passed | e75f429e02a8d5b0dd7843e113934a708590eda09a3280496a44234f0097c082 | False | 1383 | 0 |
| verify:tests | passed | 36aaf62e2f41613d3f0a2d78f35835f50706eb89439ba327cdefa0632258a1b9 | False | 2563 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5264626e664149179121ae4bef212e24 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 69dc3c268264575427f85116f5376f8694153f01832bd3d8f3193d1f819581db | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `a32a99624da29da9b74f754aa4bc04a546554ff5c2f2204531849b90f7412cb8`
