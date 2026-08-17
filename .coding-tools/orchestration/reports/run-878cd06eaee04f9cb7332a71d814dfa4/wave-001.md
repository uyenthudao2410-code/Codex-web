# Orchestration Wave 1

- Run: `878cd06eaee04f9cb7332a71d814dfa4`
- Wave: `19cca92d99974d42906a3aacb52f6fbd`
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
| 15561 | 2026-08-17T19:21:36.360Z | run_started |  | PREFLIGHT |  |
| 15562 | 2026-08-17T19:21:36.740Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15563 | 2026-08-17T19:21:36.844Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15564 | 2026-08-17T19:21:36.961Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15565 | 2026-08-17T19:21:37.071Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15566 | 2026-08-17T19:21:37.187Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15567 | 2026-08-17T19:21:37.528Z | state_transition | READY | ROUTED | reason=route_selected |
| 15568 | 2026-08-17T19:21:37.884Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=51adc8dbb0724e92aefc3401acc08398 |
| 15569 | 2026-08-17T19:21:38.023Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15570 | 2026-08-17T19:21:38.431Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=51adc8dbb0724e92aefc3401acc08398 |
| 15571 | 2026-08-17T19:21:38.542Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15572 | 2026-08-17T19:21:38.871Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8fbf345c88368916; input_fingerprint=ab9a90477cc04820a21ec288381ff2490ed3498c95d5df4cc34a8b64131dbad6 |
| 15573 | 2026-08-17T19:21:39.097Z | managed_process_admitted |  |  | owner=default |
| 15574 | 2026-08-17T19:21:39.283Z | managed_process_started |  |  | owner=default |
| 15575 | 2026-08-17T19:21:39.614Z | managed_process_terminal |  |  | owner=default |
| 15576 | 2026-08-17T19:21:39.828Z | proof_recorded |  |  | stage_id=check:8fbf345c88368916; status=passed; cache_hit=False; input_fingerprint=ab9a90477cc04820a21ec288381ff2490ed3498c95d5df4cc34a8b64131dbad6 |
| 15577 | 2026-08-17T19:21:39.974Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15578 | 2026-08-17T19:21:55.762Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15579 | 2026-08-17T19:21:56.021Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8fbf345c88368916 | passed | ab9a90477cc04820a21ec288381ff2490ed3498c95d5df4cc34a8b64131dbad6 | False | 783 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bba0fff89f8246a3a6c23a4d5e268711 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | 5e93f2ef87f2238a3bb21411a549ea83e44f33b0ad528ec929f70946d465f535 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `1dfce7556c794841e4381a53a43fdc6988b8a71e26f63e0ab5b6b26a958df6d5`
