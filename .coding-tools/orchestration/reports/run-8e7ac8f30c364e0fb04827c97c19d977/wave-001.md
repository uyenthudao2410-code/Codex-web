# Orchestration Wave 1

- Run: `8e7ac8f30c364e0fb04827c97c19d977`
- Wave: `7176830452e949eeacb9e0085fd10b62`
- Objective: Fix C01 Recovery Supervisor Scheduled Task visibility for Problem prl-22e670302757c9b7663170e226ed7c26 rev1 using the live evidence just collected. Exact evidence: the same Windows user/SID and LOCALAPPDATA are reported inside and outside Scheduled Task, but the current C:\Users\Admin\AppData\Local\WebMcpRecoverySupervisor directory and accepted supervisor script are DirectoryNotFound from the Limited Scheduled Task while visible from the Coding Tools execution sandbox; ACL grants Admin FullControl, so this is filesystem projection rather than ACL denial. The same Scheduled Task can see/read %APPDATA%\web-mcp-assistant including recovery-host.json for PID 9640, and a new subfolder/marker written there by the sandbox is visible to the task (True|True). ProgramData/Public/E: are also visible, but prefer the existing per-user Roaming data root to avoid elevation and cross-user write surfaces. Make the smallest durable fix: change Get-InstallRoot to a dedicated recovery-supervisor subdirectory under Get-DataRoot (%APPDATA%\web-mcp-assistant), retain the current direct hidden Windows PowerShell Scheduled Task action, and preserve a legacy LocalApplicationData root helper only for best-effort cleanup after the replacement supervisor has published a fresh valid heartbeat. Do not delete the legacy root before new readiness is proven. Uninstall should best-effort remove both current and legacy install roots. Update the focused source contract test and RECOVERY_HOST.md operational path/visibility explanation. Do not restart runtime, install packaged candidate, reboot, build installer, commit, push, release, or deploy in this wave.
- Objective revision: `1`
- Objective SHA-256: `10adfdb3addf1bddc50d10e452c0508247f4755b8bd487f1ef1c19e7df5903d6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `b7325226698fe70dc2b1460c2078bed2f064bdb513d1c77b938e0f5983bcb4b4`
- Contract fingerprint: `64adc198e7bde4c96465dc6929f6402e4c55ea8179f1a307417f03fc4568e7ea`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57808 | 2026-09-15T07:35:17.203Z | run_started |  | PREFLIGHT |  |
| 57809 | 2026-09-15T07:35:18.948Z | observation_span_recorded |  |  |  |
| 57810 | 2026-09-15T07:35:48.219Z | solution_shadow_recommended |  |  |  |
| 57811 | 2026-09-15T07:35:49.365Z | observation_span_recorded |  |  |  |
| 57812 | 2026-09-15T07:35:50.041Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57813 | 2026-09-15T07:35:51.721Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 57814 | 2026-09-15T07:35:52.224Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57815 | 2026-09-15T07:35:52.866Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57816 | 2026-09-15T07:35:53.907Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57817 | 2026-09-15T07:35:55.393Z | state_transition | READY | ROUTED | reason=route_selected |
| 57818 | 2026-09-15T07:35:57.742Z | observation_span_recorded |  |  |  |
| 57819 | 2026-09-15T07:35:59.251Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a38b92f152294c848bcb76cd44f9ab8b |
| 57820 | 2026-09-15T07:36:00.007Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57821 | 2026-09-15T07:36:02.098Z | observation_span_recorded |  |  |  |
| 57822 | 2026-09-15T07:36:03.141Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a38b92f152294c848bcb76cd44f9ab8b |
| 57823 | 2026-09-15T07:36:03.810Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57824 | 2026-09-15T07:36:05.002Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:387c4d3f79f45a91; input_fingerprint=8539bc6c9319900388af0da5e30979c7ace2e1c1efdfb4a80883eafc6206d4c0 |
| 57827 | 2026-09-15T07:36:09.504Z | managed_process_admitted |  |  | owner=default |
| 57829 | 2026-09-15T07:36:12.494Z | managed_process_started |  |  | owner=default |
| 57834 | 2026-09-15T07:36:38.719Z | managed_process_terminal |  |  | owner=default |
| 57835 | 2026-09-15T07:36:39.813Z | proof_recorded |  |  | stage_id=check:387c4d3f79f45a91; status=passed; cache_hit=False; input_fingerprint=8539bc6c9319900388af0da5e30979c7ace2e1c1efdfb4a80883eafc6206d4c0 |
| 57836 | 2026-09-15T07:36:40.455Z | observation_span_recorded |  |  |  |
| 57837 | 2026-09-15T07:36:41.072Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 57838 | 2026-09-15T07:36:41.714Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 57846 | 2026-09-15T07:37:53.171Z | observation_span_recorded |  |  |  |
| 57847 | 2026-09-15T07:37:53.447Z | failure_observed | ACCEPTING | ACCEPTING | reason=Rejecting this wave because it ran focused tests successfully but produced no requested source mutation: affected_files=[], patch_results=[], and completion_report.what_changed.files=[] while the supervisor still uses the old LocalApplicationData install root. Tests against unchanged source do not prove the Roaming install-root fix.; failure_class=SOL_REJECTED |
| 57848 | 2026-09-15T07:37:53.694Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 57849 | 2026-09-15T07:37:53.993Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 57853 | 2026-09-15T07:38:28.052Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:387c4d3f79f45a91 | passed | 8539bc6c9319900388af0da5e30979c7ace2e1c1efdfb4a80883eafc6206d4c0 | False | 33730 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `9f60fdae5283de9c93f97921c9edbdd993758d31b935a527da1eeff6f051481f`
