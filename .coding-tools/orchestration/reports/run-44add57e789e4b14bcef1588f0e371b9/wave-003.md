# Orchestration Wave 3

- Run: `44add57e789e4b14bcef1588f0e371b9`
- Wave: `730ddc9e526b4c4981ca1c82e257196c`
- Objective: P0.2 preflight and real Scheduled Task installation from the already fresh controlled acceptance app. Do not change source or rebuild. Require HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, acceptance root present, installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, Scheduled Task absent, supervisor root absent, healthy existing Recovery Host descriptor/process, and exactly one listener on each 18766/18767/18082/18083. Capture current Recovery Host PID+instance as the immutable baseline for this installed-session acceptance. Then invoke the installed supervisor -Action Install with installed app executable/AppRoot/Packaged and verify task structure: same current user, Interactive logon, Limited run level, fixed PowerShell action referencing %LOCALAPPDATA%\WebMcpRecoverySupervisor\recovery-supervisor.ps1 with -Action Run, two triggers, manifest mode packaged, manifest arguments exactly ['--recovery-host'], manifest executable/hash match installed app, installed supervisor copy hash exact. Return only content-free identities and task structure, never descriptor token.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12796 | 2026-08-17T08:49:44.236Z | wave_replanned |  | PREFLIGHT | reason=Raw Scheduled Task Principal.UserId string did not equal WindowsIdentity.Name. This wave changes the verification criterion to canonical SID equality and inspects current continuous-supervisor health, without changing external state. |
| 12797 | 2026-08-17T08:49:44.788Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12798 | 2026-08-17T08:49:44.987Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12799 | 2026-08-17T08:49:45.188Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12800 | 2026-08-17T08:49:45.339Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12801 | 2026-08-17T08:49:45.513Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12802 | 2026-08-17T08:49:45.701Z | state_transition | READY | ROUTED | reason=route_selected |
| 12803 | 2026-08-17T08:49:46.287Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0fe04a25ad9c48c08217679caa469e5c |
| 12804 | 2026-08-17T08:49:46.473Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12805 | 2026-08-17T08:49:46.978Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0fe04a25ad9c48c08217679caa469e5c |
| 12806 | 2026-08-17T08:49:47.169Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12807 | 2026-08-17T08:49:47.605Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ddc17c4cd7400ec7; input_fingerprint=81d2ccf2efc696b5ccf7d46614030cad0a2fba748ed8dd380545f4780b7c75d8 |
| 12808 | 2026-08-17T08:49:47.905Z | managed_process_admitted |  |  | owner=default |
| 12809 | 2026-08-17T08:49:48.195Z | managed_process_started |  |  | owner=default |
| 12810 | 2026-08-17T08:49:49.786Z | managed_process_terminal |  |  | owner=default |
| 12811 | 2026-08-17T08:49:50.187Z | proof_recorded |  |  | stage_id=check:ddc17c4cd7400ec7; status=passed; cache_hit=False; input_fingerprint=81d2ccf2efc696b5ccf7d46614030cad0a2fba748ed8dd380545f4780b7c75d8 |
| 12812 | 2026-08-17T08:49:50.478Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12813 | 2026-08-17T08:50:19.425Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12814 | 2026-08-17T08:50:19.914Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ddc17c4cd7400ec7 | passed | 81d2ccf2efc696b5ccf7d46614030cad0a2fba748ed8dd380545f4780b7c75d8 | False | 2269 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 803a6e0d1a234fcd82857059755f03d2 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 525711ac2ee76063fe9ebb69f821cbb1ad08bbad19f1856273d89778ed373bcc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `52ffb533cbbd15df0a7b36408c47f0603635ea682fdea9e7d8720b85910e4a29`
