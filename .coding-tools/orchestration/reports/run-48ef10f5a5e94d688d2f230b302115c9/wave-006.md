# Orchestration Wave 6

- Run: `48ef10f5a5e94d688d2f230b302115c9`
- Wave: `a4cf224e82164529b91ae918da1b8876`
- Objective: Complete the remaining pre-reboot C01/M02 supervisor transition for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Switch the currently suppressed development Recovery Supervisor to packaged mode for the already accepted candidate at %LOCALAPPDATA%\WebMcpAcceptance-1.0.0. Do not edit repository source, restart/stop Recovery Host/runtime, reboot/logoff, uninstall the acceptance app, clear state, commit, push, publish, release, or deploy. Success requires exact package/source supervisor bytes, exactly one candidate uninstall registration, packaged manifest/task, healthy supervisor, last_spawned_pid null, and unchanged Recovery Host PID/instance. Roll back to development+suppress on any post-mutation failure.
- Objective revision: `6`
- Objective SHA-256: `159b32c32dfbf1ad53ca5dc6d13bbe175e329de3b3d7f701105e9ed3e044a14b`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `14be24d3a8db0e7b7671336d9ab747ad8360e38101a2ee31776781d46640782b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57126 | 2026-09-15T06:57:14.265Z | wave_replanned |  | PREFLIGHT | reason=Wave 5 stopped before mutation because PowerShell flattened the single registration returned by Registrations(), so scalar PSCustomObject.Count was null and the count assertion failed. A fresh read-only registry probe now observes exactly one Coding Tools MCP 1.0.0 registration for the acceptance root. Strategy change is limited to wrapping the function result as an array with $regs=@(Registrations); all other safety checks and rollback remain unchanged. |
| 57127 | 2026-09-15T06:57:14.723Z | observation_span_recorded |  |  |  |
| 57128 | 2026-09-15T06:57:15.350Z | observation_span_recorded |  |  |  |
| 57129 | 2026-09-15T06:57:15.634Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57130 | 2026-09-15T06:57:15.849Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 57131 | 2026-09-15T06:57:16.103Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57132 | 2026-09-15T06:57:16.362Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57133 | 2026-09-15T06:57:16.707Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57134 | 2026-09-15T06:57:17.095Z | state_transition | READY | ROUTED | reason=route_selected |
| 57135 | 2026-09-15T06:57:17.414Z | observation_span_recorded |  |  |  |
| 57136 | 2026-09-15T06:57:18.411Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d136b6959f594b11877bdf0383be48ff |
| 57137 | 2026-09-15T06:57:18.853Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57140 | 2026-09-15T06:57:20.127Z | observation_span_recorded |  |  |  |
| 57141 | 2026-09-15T06:57:20.506Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d136b6959f594b11877bdf0383be48ff |
| 57142 | 2026-09-15T06:57:20.739Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57143 | 2026-09-15T06:57:21.337Z | proof_cache_miss |  |  | reason=cold; stage_id=check:af08772ff5f54f77; input_fingerprint=8c2970b3a43db857d6761ea63217d90c17a2dfd6365b3a24deef8d2748218a94 |
| 57144 | 2026-09-15T06:57:21.754Z | managed_process_admitted |  |  | owner=default |
| 57145 | 2026-09-15T06:57:22.057Z | managed_process_started |  |  | owner=default |
| 57148 | 2026-09-15T06:58:08.418Z | managed_process_terminal |  |  | owner=default |
| 57149 | 2026-09-15T06:58:08.830Z | proof_recorded |  |  | stage_id=check:af08772ff5f54f77; status=failed; cache_hit=False; input_fingerprint=8c2970b3a43db857d6761ea63217d90c17a2dfd6365b3a24deef8d2748218a94 |
| 57150 | 2026-09-15T06:58:09.078Z | observation_span_recorded |  |  |  |
| 57151 | 2026-09-15T06:58:09.315Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 57152 | 2026-09-15T06:58:09.546Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 57153 | 2026-09-15T06:58:09.837Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 57189 | 2026-09-15T07:00:29.485Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:af08772ff5f54f77 | failed | 8c2970b3a43db857d6761ea63217d90c17a2dfd6365b3a24deef8d2748218a94 | False | 47084 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `199`
- Chain head: `5df739b6b0a8862b1db29dc8a682370cffe395291baedc5598c873c88930372d`
