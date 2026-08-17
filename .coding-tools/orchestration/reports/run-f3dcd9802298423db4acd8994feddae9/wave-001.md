# Orchestration Wave 1

- Run: `f3dcd9802298423db4acd8994feddae9`
- Wave: `9d2e3ee52cd54a0e960532b709e8f728`
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
| 15541 | 2026-08-17T19:20:48.733Z | run_started |  | PREFLIGHT |  |
| 15542 | 2026-08-17T19:20:49.133Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15543 | 2026-08-17T19:20:49.248Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15544 | 2026-08-17T19:20:49.373Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15545 | 2026-08-17T19:20:49.482Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15546 | 2026-08-17T19:20:49.761Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15547 | 2026-08-17T19:20:49.923Z | state_transition | READY | ROUTED | reason=route_selected |
| 15548 | 2026-08-17T19:20:50.334Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3eb30bf868374f4ba81b1ce3938d610e |
| 15549 | 2026-08-17T19:20:50.468Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15550 | 2026-08-17T19:20:50.909Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3eb30bf868374f4ba81b1ce3938d610e |
| 15551 | 2026-08-17T19:20:51.052Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15552 | 2026-08-17T19:20:51.347Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8fbf345c88368916; input_fingerprint=68d4d7ed75f93662d5aacfcb37a25890bdc1a2a879a2f825373d1ecca01539ae |
| 15553 | 2026-08-17T19:20:51.612Z | managed_process_admitted |  |  | owner=default |
| 15554 | 2026-08-17T19:20:51.876Z | managed_process_started |  |  | owner=default |
| 15555 | 2026-08-17T19:20:52.299Z | managed_process_terminal |  |  | owner=default |
| 15556 | 2026-08-17T19:20:52.534Z | proof_recorded |  |  | stage_id=check:8fbf345c88368916; status=passed; cache_hit=False; input_fingerprint=68d4d7ed75f93662d5aacfcb37a25890bdc1a2a879a2f825373d1ecca01539ae |
| 15557 | 2026-08-17T19:20:52.641Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15558 | 2026-08-17T19:21:10.621Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15559 | 2026-08-17T19:21:10.877Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8fbf345c88368916 | passed | 68d4d7ed75f93662d5aacfcb37a25890bdc1a2a879a2f825373d1ecca01539ae | False | 903 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 81fd37be10e14c46a8e335386d51fdc3 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | 168505c7c0da645d90f0cf30745f6fdd8536bda135da01b3ddccebb1fcdb93da | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `e1b879f55d13fe6917e9ea9d7ade85eae90016bdc3ee91175ca2e43797b5dff0`
