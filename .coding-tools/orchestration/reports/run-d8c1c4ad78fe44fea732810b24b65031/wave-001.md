# Orchestration Wave 1

- Run: `d8c1c4ad78fe44fea732810b24b65031`
- Wave: `5ec0f31ecacc4b5fa0b582f146ba9a72`
- Objective: Pre-P3 live acceptance after authorized runtime restart: verify P0 ExceptionGroup normalization is loaded and focused tests pass; verify P1 evaluation/controller/quality instrumentation reporters remain consistent; verify P2 rework diagnosis/readiness metrics remain valid. Read-only verification only: do not modify product source or public contracts.
- Mode: `mcp_only`
- Base HEAD: `bc07e240740726d9a5ddbd590e01568344a92440`
- Worktree fingerprint: `7aa7dd66c9489dc8071ba6f75b0b0de0aad2c2caf46c08311f850501c3092120`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15629 | 2026-08-17T19:44:51.537Z | run_started |  | PREFLIGHT |  |
| 15630 | 2026-08-17T19:44:51.949Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15631 | 2026-08-17T19:44:52.217Z | managed_process_admitted |  |  | owner=default |
| 15632 | 2026-08-17T19:44:52.444Z | managed_process_started |  |  | owner=default |
| 15633 | 2026-08-17T19:44:54.751Z | managed_process_terminal |  |  | owner=default |
| 15634 | 2026-08-17T19:44:54.879Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15635 | 2026-08-17T19:44:54.987Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15636 | 2026-08-17T19:44:55.105Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15637 | 2026-08-17T19:44:55.217Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15638 | 2026-08-17T19:44:55.368Z | state_transition | READY | ROUTED | reason=route_selected |
| 15639 | 2026-08-17T19:44:55.755Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=75f6fd04241b4e9f9445246bf18af98d |
| 15640 | 2026-08-17T19:44:55.868Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15641 | 2026-08-17T19:44:56.318Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=75f6fd04241b4e9f9445246bf18af98d |
| 15642 | 2026-08-17T19:44:56.484Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15643 | 2026-08-17T19:44:56.785Z | proof_cache_miss |  |  | reason=cold; stage_id=check:38f8c7ca840a9e3b; input_fingerprint=c2c09a6eae9c3c95d8493fa2c43e5b8fa746a1a2cfbfe9b690a90346831e7b05 |
| 15644 | 2026-08-17T19:44:57.053Z | managed_process_admitted |  |  | owner=default |
| 15645 | 2026-08-17T19:44:57.334Z | managed_process_started |  |  | owner=default |
| 15646 | 2026-08-17T19:45:00.984Z | managed_process_terminal |  |  | owner=default |
| 15647 | 2026-08-17T19:45:01.207Z | proof_recorded |  |  | stage_id=check:38f8c7ca840a9e3b; status=passed; cache_hit=False; input_fingerprint=c2c09a6eae9c3c95d8493fa2c43e5b8fa746a1a2cfbfe9b690a90346831e7b05 |
| 15648 | 2026-08-17T19:45:01.357Z | proof_cache_miss |  |  | reason=cold; stage_id=check:30f82e9ed2f048a4; input_fingerprint=5cda1dfb07854dad570fe36adcae91ba97bcbe9a062d1f138f2b985b71c3bf84 |
| 15649 | 2026-08-17T19:45:01.649Z | managed_process_admitted |  |  | owner=default |
| 15650 | 2026-08-17T19:45:01.902Z | managed_process_started |  |  | owner=default |
| 15651 | 2026-08-17T19:45:03.869Z | managed_process_terminal |  |  | owner=default |
| 15652 | 2026-08-17T19:45:04.187Z | proof_recorded |  |  | stage_id=check:30f82e9ed2f048a4; status=passed; cache_hit=False; input_fingerprint=5cda1dfb07854dad570fe36adcae91ba97bcbe9a062d1f138f2b985b71c3bf84 |
| 15653 | 2026-08-17T19:45:04.305Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=596b39681b5e829e39b73252fb7d4fd86709cfc8e7da145c092b53587c98ca37 |
| 15654 | 2026-08-17T19:45:04.535Z | managed_process_admitted |  |  | owner=default |
| 15655 | 2026-08-17T19:45:04.755Z | managed_process_started |  |  | owner=default |
| 15656 | 2026-08-17T19:45:05.085Z | managed_process_terminal |  |  | owner=default |
| 15657 | 2026-08-17T19:45:05.330Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=596b39681b5e829e39b73252fb7d4fd86709cfc8e7da145c092b53587c98ca37 |
| 15658 | 2026-08-17T19:45:05.464Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c912449a7752543053c80aa321331b57c01c674ba37efe96d6d83eec4328cc92 |
| 15659 | 2026-08-17T19:45:05.752Z | managed_process_admitted |  |  | owner=default |
| 15660 | 2026-08-17T19:45:05.987Z | managed_process_started |  |  | owner=default |
| 15661 | 2026-08-17T19:45:08.136Z | managed_process_terminal |  |  | owner=default |
| 15662 | 2026-08-17T19:45:09.255Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c912449a7752543053c80aa321331b57c01c674ba37efe96d6d83eec4328cc92 |
| 15663 | 2026-08-17T19:45:09.420Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15664 | 2026-08-17T19:50:04.493Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15665 | 2026-08-17T19:50:04.763Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:38f8c7ca840a9e3b | passed | c2c09a6eae9c3c95d8493fa2c43e5b8fa746a1a2cfbfe9b690a90346831e7b05 | False | 4187 | 0 |
| check:30f82e9ed2f048a4 | passed | 5cda1dfb07854dad570fe36adcae91ba97bcbe9a062d1f138f2b985b71c3bf84 | False | 2558 | 0 |
| check:80a1a46bd01d26a3 | passed | 596b39681b5e829e39b73252fb7d4fd86709cfc8e7da145c092b53587c98ca37 | False | 814 | 0 |
| verify:tests | passed | c912449a7752543053c80aa321331b57c01c674ba37efe96d6d83eec4328cc92 | False | 3469 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 8c989678662b48adb5847a78aeaa4395 | accepted | bc07e240740726d9a5ddbd590e01568344a92440 | 4ee082e37cc594ce1c6e973134d53ea409c7041c39ed2080c8e79c508e58d1e1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `3b37664bc6c16f85913ad52dcb9deedf2e155afc4d72a6e4ad894fcdb5623135`
