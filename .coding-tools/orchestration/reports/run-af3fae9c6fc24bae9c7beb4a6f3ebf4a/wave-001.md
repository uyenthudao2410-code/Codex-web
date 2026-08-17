# Orchestration Wave 1

- Run: `af3fae9c6fc24bae9c7beb4a6f3ebf4a`
- Wave: `54e3e9dd50a54149b8e79f45b4f61919`
- Objective: P1 synthetic instrumentation smoke: verify the current Git HEAD identity read-only. This run exists only to validate evaluation enrollment/plumbing and must not be used as efficacy evidence.
- Mode: `mcp_only`
- Base HEAD: `775d92716f90ada3cfa909d8f0069c46d204ab51`
- Worktree fingerprint: `c8e09216432e7ead7ec2792b7f3a354b61d9ca7fc4bb2bc610f5136e9976bfca`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15521 | 2026-08-17T19:19:03.860Z | run_started |  | PREFLIGHT |  |
| 15522 | 2026-08-17T19:19:04.279Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15523 | 2026-08-17T19:19:04.396Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15524 | 2026-08-17T19:19:04.512Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15525 | 2026-08-17T19:19:04.636Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15526 | 2026-08-17T19:19:04.745Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15527 | 2026-08-17T19:19:04.878Z | state_transition | READY | ROUTED | reason=route_selected |
| 15528 | 2026-08-17T19:19:05.261Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=acfade50e98b4283bcd7d9008d4f0d40 |
| 15529 | 2026-08-17T19:19:05.395Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15530 | 2026-08-17T19:19:05.761Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=acfade50e98b4283bcd7d9008d4f0d40 |
| 15531 | 2026-08-17T19:19:05.890Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15532 | 2026-08-17T19:19:06.200Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8fbf345c88368916; input_fingerprint=ce92d9d9a16014278fc4070e0f94c98d67141e6b93f202d401cfc568252e6348 |
| 15533 | 2026-08-17T19:19:06.462Z | managed_process_admitted |  |  | owner=default |
| 15534 | 2026-08-17T19:19:06.669Z | managed_process_started |  |  | owner=default |
| 15535 | 2026-08-17T19:19:07.092Z | managed_process_terminal |  |  | owner=default |
| 15536 | 2026-08-17T19:19:07.316Z | proof_recorded |  |  | stage_id=check:8fbf345c88368916; status=passed; cache_hit=False; input_fingerprint=ce92d9d9a16014278fc4070e0f94c98d67141e6b93f202d401cfc568252e6348 |
| 15537 | 2026-08-17T19:19:07.498Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15538 | 2026-08-17T19:20:11.918Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15539 | 2026-08-17T19:20:12.184Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8fbf345c88368916 | passed | ce92d9d9a16014278fc4070e0f94c98d67141e6b93f202d401cfc568252e6348 | False | 884 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 57bc7f94b60d4eccb1d8bc85770eb512 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | 1d9e922c898fc90da9de9d33da92d4fc6ae97a89aebcbfaa56949d1d7c90f1fb | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `1376bbbe71d9c7868c53841707730e71f7329178df7bc1d4070788123da6faee`
