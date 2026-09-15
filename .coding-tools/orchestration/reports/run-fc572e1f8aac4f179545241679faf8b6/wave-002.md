# Orchestration Wave 2

- Run: `fc572e1f8aac4f179545241679faf8b6`
- Wave: `c8e2957282f14ba9a9d7168d08440ff3`
- Objective: Replan C01/M02 pre-reboot wave A in the same canonical engineering attempt after the previous harness-only failure. Persist the accepted NSIS candidate dist/coding-tools-mcp-setup-1.0.0.exe into %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 only after robust per-entry registry normalization proves the target is absent. Preserve the current development Recovery Host and current development WebMCP Recovery Supervisor Scheduled Task byte/identity definition unchanged. Verify installed executable, uninstaller, registry registration, packaged supervisor source hash, production Recovery Host descriptor owner/instance stability, and Scheduled Task XML fingerprint stability. Do not install/replace/start the packaged Recovery Supervisor yet; do not remove stop.request; do not restart runtime, reboot/logoff, edit source, clear state, commit, push, publish, release, or deploy. If NSIS succeeds but a post-install assertion fails, silently uninstall only this new acceptance app before returning failure.
- Objective revision: `2`
- Objective SHA-256: `0227b26e8c4294cd719b34f898894e2b5e36edd44b7ecc86898ef4adc476c811`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `85bfde77bd0bb948241b5b86a52fbc61fb963a9f76d1a4ade3030c36946c99fc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 56964 | 2026-09-15T06:41:48.688Z | wave_replanned |  | PREFLIGHT | reason=Previous wave failed before NSIS mutation because the registry helper called Path.GetFullPath inside Where-Object over arbitrary uninstall entries and hit an invalid/malformed InstallLocation. No source or external installation mutation occurred. The new strategy enumerates each uninstall entry explicitly, normalizes each InstallLocation under try/catch, ignores malformed entries, and hashes Scheduled Task XML using Export-ScheduledTask. All product/candidate invariants and the app-only scope remain unchanged. |
| 56965 | 2026-09-15T06:41:49.228Z | observation_span_recorded |  |  |  |
| 56966 | 2026-09-15T06:41:49.787Z | observation_span_recorded |  |  |  |
| 56967 | 2026-09-15T06:41:50.283Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 56968 | 2026-09-15T06:41:50.566Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 56969 | 2026-09-15T06:41:50.901Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 56970 | 2026-09-15T06:41:51.122Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 56971 | 2026-09-15T06:41:51.424Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 56972 | 2026-09-15T06:41:51.750Z | state_transition | READY | ROUTED | reason=route_selected |
| 56973 | 2026-09-15T06:41:52.122Z | observation_span_recorded |  |  |  |
| 56974 | 2026-09-15T06:41:52.965Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f1874a0be96349cb981e35969c76569e |
| 56975 | 2026-09-15T06:41:53.312Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 56976 | 2026-09-15T06:41:54.144Z | observation_span_recorded |  |  |  |
| 56977 | 2026-09-15T06:41:54.780Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f1874a0be96349cb981e35969c76569e |
| 56978 | 2026-09-15T06:41:55.134Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 56979 | 2026-09-15T06:41:55.803Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2a982673a35643e1; input_fingerprint=72050ca7e6ed90ceaaea06b578fdd96a8115f8dafd6899ee66cd6d6f7651c686 |
| 56980 | 2026-09-15T06:41:56.566Z | managed_process_admitted |  |  | owner=default |
| 56981 | 2026-09-15T06:41:57.166Z | managed_process_started |  |  | owner=default |
| 56987 | 2026-09-15T06:42:33.086Z | managed_process_terminal |  |  | owner=default |
| 56988 | 2026-09-15T06:42:33.473Z | proof_recorded |  |  | stage_id=check:2a982673a35643e1; status=failed; cache_hit=False; input_fingerprint=72050ca7e6ed90ceaaea06b578fdd96a8115f8dafd6899ee66cd6d6f7651c686 |
| 56989 | 2026-09-15T06:42:33.750Z | observation_span_recorded |  |  |  |
| 56990 | 2026-09-15T06:42:33.968Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 56991 | 2026-09-15T06:42:34.132Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 56992 | 2026-09-15T06:42:34.389Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 56993 | 2026-09-15T06:42:50.224Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2a982673a35643e1 | failed | 72050ca7e6ed90ceaaea06b578fdd96a8115f8dafd6899ee66cd6d6f7651c686 | False | 37079 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `0c006a821b788c3fd064513531d1376fb7117c3732b8af155ab03e9518736245`
