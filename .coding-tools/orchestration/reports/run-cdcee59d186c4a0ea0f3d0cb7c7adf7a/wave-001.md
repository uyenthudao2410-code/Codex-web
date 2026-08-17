# Orchestration Wave 1

- Run: `cdcee59d186c4a0ea0f3d0cb7c7adf7a`
- Wave: `9b393d0774e248e59443dffb684afd4c`
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
| 15581 | 2026-08-17T19:22:22.577Z | run_started |  | PREFLIGHT |  |
| 15582 | 2026-08-17T19:22:22.960Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15583 | 2026-08-17T19:22:23.069Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15584 | 2026-08-17T19:22:23.195Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15585 | 2026-08-17T19:22:23.311Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15586 | 2026-08-17T19:22:23.401Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15587 | 2026-08-17T19:22:23.494Z | state_transition | READY | ROUTED | reason=route_selected |
| 15588 | 2026-08-17T19:22:23.860Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=aa0ee830ef0545bcb912f6689ad03664 |
| 15589 | 2026-08-17T19:22:23.977Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15590 | 2026-08-17T19:22:24.349Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=aa0ee830ef0545bcb912f6689ad03664 |
| 15591 | 2026-08-17T19:22:24.481Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15592 | 2026-08-17T19:22:24.788Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8fbf345c88368916; input_fingerprint=7f15ebe6cb484742ca721f3727c2e4f8c5d41775bc28783f2c3bf8224579faed |
| 15593 | 2026-08-17T19:22:25.093Z | managed_process_admitted |  |  | owner=default |
| 15594 | 2026-08-17T19:22:25.310Z | managed_process_started |  |  | owner=default |
| 15595 | 2026-08-17T19:22:25.619Z | managed_process_terminal |  |  | owner=default |
| 15596 | 2026-08-17T19:22:25.830Z | proof_recorded |  |  | stage_id=check:8fbf345c88368916; status=passed; cache_hit=False; input_fingerprint=7f15ebe6cb484742ca721f3727c2e4f8c5d41775bc28783f2c3bf8224579faed |
| 15597 | 2026-08-17T19:22:25.950Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15598 | 2026-08-17T19:22:40.131Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15599 | 2026-08-17T19:22:40.405Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8fbf345c88368916 | passed | 7f15ebe6cb484742ca721f3727c2e4f8c5d41775bc28783f2c3bf8224579faed | False | 778 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 38a88767cf924e45bb05a8265976a31b | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | eb0a76425754d6839d3360576809eec8fb92cf319cde0a5c40fb9d64e22015b9 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `cb39d1e62513b7d4e2f7882dcf46c8a2a4cd62d3dbce9385b909dcf8c3de9c96`
