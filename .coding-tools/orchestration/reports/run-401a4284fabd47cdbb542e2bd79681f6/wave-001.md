# Orchestration Wave 1

- Run: `401a4284fabd47cdbb542e2bd79681f6`
- Wave: `cc6d939a32f94c28a6f9bdc811c1eb05`
- Objective: C01/M02 machine-A candidate replacement step for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Replace only the stale persistent acceptance installation at %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 with the already-checkpointed fresh NSIS artifact dist\coding-tools-mcp-setup-1.0.0.exe whose exact SHA256 is a2b6fe2d168af983e5a21c461453593f71be3b5609d14172b770fb5d3155d887 and size is 121749108. Before mutation, prove the installer identity and prove the existing acceptance installation is stale. Perform a bounded silent uninstall/reinstall only for that acceptance root, then verify installed Coding Tools MCP.exe SHA256 exactly cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c, installed recovery-supervisor.ps1 SHA256 exactly 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab, launcher SHA256 exactly 082d4b2a8c5cc40a76b778c8503f29c6985edc3e8b3f6d688a205416e9b23a90, and exactly one matching uninstall registration. Prove the currently running production Recovery Host identity and Recovery Supervisor manifest/task are unchanged across this candidate replacement. Do not change production Recovery Supervisor mode yet. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy. If any postcondition fails, rollback to a clean acceptance installation state without touching the production Recovery Supervisor.
- Objective revision: `1`
- Objective SHA-256: `071763ba6d369f94b1bd16a534131fa60794bc3f94634ebce8a02f4eba4531bd`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58652 | 2026-09-15T08:58:18.956Z | run_started |  | PREFLIGHT |  |
| 58653 | 2026-09-15T08:58:19.822Z | observation_span_recorded |  |  |  |
| 58654 | 2026-09-15T08:58:20.267Z | solution_shadow_recommended |  |  |  |
| 58655 | 2026-09-15T08:58:26.318Z | observation_span_recorded |  |  |  |
| 58656 | 2026-09-15T08:58:26.667Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58669 | 2026-09-15T09:00:41.188Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58670 | 2026-09-15T09:00:41.468Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58671 | 2026-09-15T09:00:42.005Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58672 | 2026-09-15T09:00:42.315Z | state_transition | READY | ROUTED | reason=route_selected |
| 58673 | 2026-09-15T09:00:42.672Z | observation_span_recorded |  |  |  |
| 58674 | 2026-09-15T09:00:43.651Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e93f64cf8fac43eebd760e3b38cfb0e8 |
| 58675 | 2026-09-15T09:00:43.974Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58676 | 2026-09-15T09:00:44.688Z | observation_span_recorded |  |  |  |
| 58677 | 2026-09-15T09:00:45.216Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e93f64cf8fac43eebd760e3b38cfb0e8 |
| 58678 | 2026-09-15T09:00:45.544Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58679 | 2026-09-15T09:00:46.388Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e75942ac9c1ea8a3; input_fingerprint=834d67968bce154935aba891682560a458d69ff798839a6ef379c9d3e3d07344 |
| 58680 | 2026-09-15T09:00:47.030Z | managed_process_admitted |  |  | owner=default |
| 58681 | 2026-09-15T09:00:47.646Z | managed_process_started |  |  | owner=default |
| 58686 | 2026-09-15T09:01:17.711Z | managed_process_terminal |  |  | owner=default |
| 58687 | 2026-09-15T09:01:18.623Z | proof_recorded |  |  | stage_id=check:e75942ac9c1ea8a3; status=passed; cache_hit=False; input_fingerprint=834d67968bce154935aba891682560a458d69ff798839a6ef379c9d3e3d07344 |
| 58688 | 2026-09-15T09:01:18.971Z | observation_span_recorded |  |  |  |
| 58689 | 2026-09-15T09:01:20.220Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 58690 | 2026-09-15T09:01:20.866Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 58691 | 2026-09-15T09:01:56.201Z | continuity_telemetry_recorded |  |  |  |
| 58692 | 2026-09-15T09:02:08.452Z | quality_outcome_recorded |  |  |  |
| 58693 | 2026-09-15T09:02:08.646Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 58694 | 2026-09-15T09:02:09.037Z | observation_span_recorded |  |  |  |
| 58695 | 2026-09-15T09:02:09.228Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 58696 | 2026-09-15T09:02:09.460Z | observation_span_recorded |  |  |  |
| 58697 | 2026-09-15T09:02:09.676Z | observation_span_recorded |  |  |  |
| 58698 | 2026-09-15T09:02:09.913Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e75942ac9c1ea8a3 | passed | 834d67968bce154935aba891682560a458d69ff798839a6ef379c9d3e3d07344 | False | 31390 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ba25cde4ba744c0bb7595aab65ae4bec | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 00743f546ee49f4a7eecb2fd832572bb53585199ccd7473d4f6a4d163d9b835b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `bf0ee871cc2bb1b160c7a20aceb54bd1184fa5150024b301810992da4912b808`
