# Orchestration Wave 1

- Run: `2bc2b16616de4077857003881bd16256`
- Wave: `ad40dc80d3f949c2b3d3cd32ae698bcd`
- Objective: C01/M02 machine-A packaged Recovery Supervisor transition for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. The fresh persistent acceptance candidate is now checkpointed and installed at %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 with executable SHA256 cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c and recovery-supervisor.ps1 SHA256 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab. Transition the independent Recovery Supervisor from current development mode to packaged mode using the installed candidate's supervisor script and executable. Before mutation, prove current manifest mode=development, supervisor state=healthy, Scheduled Task exists, and live Recovery Host owner PID/instance are healthy. Invoke only the installed supervisor's -Action Install -Packaged with Executable=<acceptance root>\Coding Tools MCP.exe and AppRoot=<acceptance root>. Postconditions must prove: installed supervisor manifest mode=packaged; executable/app_root exact; arguments exactly ['--recovery-host']; executable SHA and installed script/launcher hashes exact; stop.request absent; Scheduled Task action uses direct Windows PowerShell on the installed supervisor script with same-user Interactive/Limited principal and AtLogOn plus one-minute repetition semantics; supervisor state healthy with live supervisor PID; Recovery Host owner PID and instance_id exactly unchanged from pre-transition; status last_host_pid/last_host_instance_id match that host; last_spawned_pid is null, proving adoption instead of spawn. If transition or any postcondition fails after mutation, rollback to development supervisor from E:\DEV\Codex-web\resources\recovery-supervisor\recovery-supervisor.ps1 using E:\DEV\Codex-web\node_modules\electron\dist\electron.exe and AppRoot E:\DEV\Codex-web, then verify development health. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy.
- Objective revision: `1`
- Objective SHA-256: `05413466b7844bfeee524ae6a005ff62f9815de39d17eded27c804270be2a90c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58699 | 2026-09-15T09:05:07.728Z | run_started |  | PREFLIGHT |  |
| 58700 | 2026-09-15T09:05:08.738Z | observation_span_recorded |  |  |  |
| 58701 | 2026-09-15T09:05:09.165Z | solution_shadow_recommended |  |  |  |
| 58702 | 2026-09-15T09:05:15.827Z | observation_span_recorded |  |  |  |
| 58703 | 2026-09-15T09:05:16.402Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58711 | 2026-09-15T09:07:01.698Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58712 | 2026-09-15T09:07:02.098Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58713 | 2026-09-15T09:07:02.408Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58714 | 2026-09-15T09:07:02.919Z | state_transition | READY | ROUTED | reason=route_selected |
| 58715 | 2026-09-15T09:07:03.346Z | observation_span_recorded |  |  |  |
| 58716 | 2026-09-15T09:07:04.593Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=81395622e5ef44f988c0324856b8d1f0 |
| 58717 | 2026-09-15T09:07:05.028Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58718 | 2026-09-15T09:07:05.851Z | observation_span_recorded |  |  |  |
| 58719 | 2026-09-15T09:07:06.449Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=81395622e5ef44f988c0324856b8d1f0 |
| 58720 | 2026-09-15T09:07:06.773Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58721 | 2026-09-15T09:07:07.482Z | proof_cache_miss |  |  | reason=cold; stage_id=check:42f6b1c4f0318c96; input_fingerprint=37e7729f670bf83f11583cce49649262471fc45005d8214ef47a2402da2622d5 |
| 58722 | 2026-09-15T09:07:08.176Z | observation_span_recorded |  |  |  |
| 58723 | 2026-09-15T09:07:08.696Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 58724 | 2026-09-15T09:07:09.048Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 58725 | 2026-09-15T09:07:09.299Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `a1b6c357935ccb198a60f090f208d3c0dbec36c62138d7762fa8ed0a545815c5`
