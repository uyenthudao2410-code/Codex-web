# Orchestration Wave 1

- Run: `44add57e789e4b14bcef1588f0e371b9`
- Wave: `756902de176d4468acf62430864595a6`
- Objective: P0.2 preflight and real Scheduled Task installation from the already fresh controlled acceptance app. Do not change source or rebuild. Require HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, acceptance root present, installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, Scheduled Task absent, supervisor root absent, healthy existing Recovery Host descriptor/process, and exactly one listener on each 18766/18767/18082/18083. Capture current Recovery Host PID+instance as the immutable baseline for this installed-session acceptance. Then invoke the installed supervisor -Action Install with installed app executable/AppRoot/Packaged and verify task structure: same current user, Interactive logon, Limited run level, fixed PowerShell action referencing %LOCALAPPDATA%\WebMcpRecoverySupervisor\recovery-supervisor.ps1 with -Action Run, two triggers, manifest mode packaged, manifest arguments exactly ['--recovery-host'], manifest executable/hash match installed app, installed supervisor copy hash exact. Return only content-free identities and task structure, never descriptor token.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12753 | 2026-08-17T08:48:09.804Z | run_started |  | PREFLIGHT |  |
| 12754 | 2026-08-17T08:48:10.290Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12755 | 2026-08-17T08:48:10.522Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12756 | 2026-08-17T08:48:10.675Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12757 | 2026-08-17T08:48:10.869Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12758 | 2026-08-17T08:48:11.123Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12759 | 2026-08-17T08:48:11.307Z | state_transition | READY | ROUTED | reason=route_selected |
| 12760 | 2026-08-17T08:48:11.837Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f54b71566678451da1ba0d6b390edff5 |
| 12761 | 2026-08-17T08:48:12.029Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12762 | 2026-08-17T08:48:12.562Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f54b71566678451da1ba0d6b390edff5 |
| 12763 | 2026-08-17T08:48:12.770Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12764 | 2026-08-17T08:48:13.197Z | proof_cache_miss |  |  | reason=cold; stage_id=check:06b6bce1314b8479; input_fingerprint=13be00232f33fbda513264e5f55e1d0da81bd329c7ef6a2a6d18afaf1a1222b2 |
| 12765 | 2026-08-17T08:48:13.572Z | managed_process_admitted |  |  | owner=default |
| 12766 | 2026-08-17T08:48:13.887Z | managed_process_started |  |  | owner=default |
| 12767 | 2026-08-17T08:48:16.860Z | managed_process_terminal |  |  | owner=default |
| 12768 | 2026-08-17T08:48:17.360Z | proof_recorded |  |  | stage_id=check:06b6bce1314b8479; status=passed; cache_hit=False; input_fingerprint=13be00232f33fbda513264e5f55e1d0da81bd329c7ef6a2a6d18afaf1a1222b2 |
| 12769 | 2026-08-17T08:48:17.579Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1e58c4ae1ad9913d; input_fingerprint=177a784cf33ab0b4c46dcc11c241e1deec770828bbdb84cba499650873b4486a |
| 12770 | 2026-08-17T08:48:17.914Z | managed_process_admitted |  |  | owner=default |
| 12771 | 2026-08-17T08:48:18.273Z | managed_process_started |  |  | owner=default |
| 12772 | 2026-08-17T08:48:22.498Z | managed_process_terminal |  |  | owner=default |
| 12773 | 2026-08-17T08:48:22.902Z | proof_recorded |  |  | stage_id=check:1e58c4ae1ad9913d; status=failed; cache_hit=False; input_fingerprint=177a784cf33ab0b4c46dcc11c241e1deec770828bbdb84cba499650873b4486a |
| 12774 | 2026-08-17T08:48:23.133Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12775 | 2026-08-17T08:48:23.315Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12776 | 2026-08-17T08:48:23.524Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:06b6bce1314b8479 | passed | 13be00232f33fbda513264e5f55e1d0da81bd329c7ef6a2a6d18afaf1a1222b2 | False | 3629 | 0 |
| check:1e58c4ae1ad9913d | failed | 177a784cf33ab0b4c46dcc11c241e1deec770828bbdb84cba499650873b4486a | False | 4961 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `52ffb533cbbd15df0a7b36408c47f0603635ea682fdea9e7d8720b85910e4a29`
