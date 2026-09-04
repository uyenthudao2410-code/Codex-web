# Orchestration Wave 1

- Run: `4f90b1d2e37443f6a16f9f8a1d327316`
- Wave: `d550c5df3bd44ecbb07c3cef2d73bfa7`
- Objective: G2-P11 provenance closure ONLY for the exact current supported exact patch/write packet. Adopt without changing source bytes exactly resources/coding-tools-mcp/coding_tools_mcp/file_tools.py SHA-256 a3b03c04a96e59217cde73673fb2aa0536bb8f4adbc3ecdd7f2c1c8c84291228; resources/coding-tools-mcp/coding_tools_mcp/patching.py SHA-256 49cab7fad66ef8cf0bfcc3aa084a92d3579cab9d9104210e4ca8065d56461320; resources/coding-tools-mcp/tests/test_exact_patch_write.py SHA-256 d34fb3e1db75b63219211d6ef43dfe919b0523de64d9f7506038e116a6b32546. Causal objective: supported exact patch/write path accepts zlib-base64 exact UTF-8 payload with mandatory preimage/postimage SHA-256; enforces an 8 MiB decompressed limit; preserves mixed line endings; stages atomically; preimage mismatch or invalid/oversize payload stages nothing and fails closed. Preserve the dirty worktree and all .coding-tools evidence. No source outside these three paths; no direct SQLite; no stale-RUN reconciliation; no bulk adopt; no synthetic Problems/outcomes/cohorts; no reset/restore/clean/rebase; no secret output; no commit/push/tag/release/publish/deploy.
- Objective revision: `1`
- Objective SHA-256: `5b9bd89c2fb0879777b33267f4d190cd21b10cd4797344b27bc62946d63ac2a3`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: `bb2f0037a43940b64fc2cd05c4f7443a06cb5abd782d76beb581e29be26d0203`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38404 | 2026-09-03T17:57:39.711Z | run_started |  | PREFLIGHT |  |
| 38405 | 2026-09-03T17:57:40.148Z | observation_span_recorded |  |  |  |
| 38406 | 2026-09-03T17:57:41.020Z | observation_span_recorded |  |  |  |
| 38407 | 2026-09-03T17:57:41.256Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38408 | 2026-09-03T17:57:41.456Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38409 | 2026-09-03T17:57:41.648Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38410 | 2026-09-03T17:57:41.865Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38411 | 2026-09-03T17:57:42.094Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38412 | 2026-09-03T17:57:42.311Z | state_transition | READY | ROUTED | reason=route_selected |
| 38413 | 2026-09-03T17:57:42.519Z | observation_span_recorded |  |  |  |
| 38414 | 2026-09-03T17:57:43.463Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b1526a44340c4fb2953503b1f73c5594 |
| 38415 | 2026-09-03T17:57:43.691Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38416 | 2026-09-03T17:57:44.566Z | existing_file_adoption_observed |  |  |  |
| 38417 | 2026-09-03T17:57:44.803Z | observation_span_recorded |  |  |  |
| 38418 | 2026-09-03T17:57:45.177Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b1526a44340c4fb2953503b1f73c5594 |
| 38419 | 2026-09-03T17:57:45.370Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38420 | 2026-09-03T17:57:46.274Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0f82724bf6b53888; input_fingerprint=2b7bbe775da6e8a103dd0bfa8da02fc25151859f415ba6e75c1c58069304d783 |
| 38421 | 2026-09-03T17:57:46.703Z | managed_process_admitted |  |  | owner=default |
| 38422 | 2026-09-03T17:57:47.140Z | managed_process_started |  |  | owner=default |
| 38423 | 2026-09-03T17:57:47.663Z | managed_process_terminal |  |  | owner=default |
| 38424 | 2026-09-03T17:57:48.035Z | proof_recorded |  |  | stage_id=check:0f82724bf6b53888; status=passed; cache_hit=False; input_fingerprint=2b7bbe775da6e8a103dd0bfa8da02fc25151859f415ba6e75c1c58069304d783 |
| 38425 | 2026-09-03T17:57:48.249Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d2068e10c89a2e53; input_fingerprint=3dd3b3ed4b62f90697c1f004d7c90d1a3b7822767f0ddb3384638c0a20b0cf0c |
| 38426 | 2026-09-03T17:57:48.673Z | managed_process_admitted |  |  | owner=default |
| 38427 | 2026-09-03T17:57:49.363Z | managed_process_started |  |  | owner=default |
| 38428 | 2026-09-03T17:57:50.629Z | managed_process_terminal |  |  | owner=default |
| 38429 | 2026-09-03T17:57:51.020Z | proof_recorded |  |  | stage_id=check:d2068e10c89a2e53; status=passed; cache_hit=False; input_fingerprint=3dd3b3ed4b62f90697c1f004d7c90d1a3b7822767f0ddb3384638c0a20b0cf0c |
| 38430 | 2026-09-03T17:57:51.212Z | observation_span_recorded |  |  |  |
| 38431 | 2026-09-03T17:57:51.454Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38432 | 2026-09-03T17:58:10.063Z | quality_outcome_recorded |  |  |  |
| 38433 | 2026-09-03T17:58:10.314Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38434 | 2026-09-03T17:58:10.610Z | observation_span_recorded |  |  |  |
| 38435 | 2026-09-03T17:58:10.978Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:0f82724bf6b53888 | passed | 2b7bbe775da6e8a103dd0bfa8da02fc25151859f415ba6e75c1c58069304d783 | False | 1373 | 0 |
| check:d2068e10c89a2e53 | passed | 3dd3b3ed4b62f90697c1f004d7c90d1a3b7822767f0ddb3384638c0a20b0cf0c | False | 2437 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| adc77a73f41442638bc80f4fe46d502e | accepted | 80aceb583202ad381c25687969fb48adbf74622c | b65085af4c409219a58ec640014dc50ce4c7981bd41594c32df58db2e01e9097 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `13458dd434be8b347179f5e3645bb166590fa8274c871209f51e481a302dd80e`
