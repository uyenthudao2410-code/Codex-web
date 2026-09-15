# Orchestration Wave 2

- Run: `8e7ac8f30c364e0fb04827c97c19d977`
- Wave: `4a6f9f229c72435994fd08e65b5d056a`
- Objective: Apply the previously diagnosed C01 Recovery Supervisor host-visibility fix for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Move the installed supervisor bytes from the Codex-sandbox-projected LocalApplicationData root to the already proven host-visible per-user Roaming data root %APPDATA%\web-mcp-assistant\recovery-supervisor. Preserve the old LocalApplicationData path only as a legacy migration target. During replacement, signal both current and legacy stop sentinels when the legacy directory exists; after and only after the new supervisor publishes a fresh valid heartbeat, best-effort remove the legacy install root. Uninstall best-effort removes both roots. Keep the direct hidden Windows PowerShell task action. Add focused static contract coverage and update RECOVERY_HOST.md. Do not restart runtime, install the live supervisor, build installer, reboot, commit, push, release, or deploy in this wave.
- Objective revision: `2`
- Objective SHA-256: `2eddb2aebd9972a03f04e33f26be4003c21f67cafc77f2127f79fa7db0870e19`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `7f15ecbb827218743b2d29f42c40d75d9d9524a1e36a025d86c59a98d3110083`
- Contract fingerprint: `64adc198e7bde4c96465dc6929f6402e4c55ea8179f1a307417f03fc4568e7ea`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57882 | 2026-09-15T07:39:22.160Z | wave_replanned |  | PREFLIGHT | reason=Previous wave was rejected because it was a no-op: it ran the focused tests but did not apply any source mutation. This wave supplies an explicit bounded patch implementing the already-proven host-visible Roaming install-root strategy and migration safeguards. |
| 57883 | 2026-09-15T07:39:22.574Z | observation_span_recorded |  |  |  |
| 57884 | 2026-09-15T07:39:57.337Z | observation_span_recorded |  |  |  |
| 57885 | 2026-09-15T07:39:57.569Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57886 | 2026-09-15T07:39:57.818Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57887 | 2026-09-15T07:39:58.045Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57888 | 2026-09-15T07:39:58.276Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 57889 | 2026-09-15T07:39:58.601Z | state_transition | READY | ROUTED | reason=route_selected |
| 57890 | 2026-09-15T07:39:58.886Z | observation_span_recorded |  |  |  |
| 57891 | 2026-09-15T07:39:59.589Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=76effebfcd63446b95c3e526d8375539 |
| 57892 | 2026-09-15T07:39:59.833Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57893 | 2026-09-15T07:40:00.510Z | observation_span_recorded |  |  |  |
| 57894 | 2026-09-15T07:40:00.744Z | failure_observed | EXECUTING | EXECUTING | failure_class=SOURCE_DRIFT |
| 57895 | 2026-09-15T07:40:01.029Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=76effebfcd63446b95c3e526d8375539 |
| 57896 | 2026-09-15T07:40:01.269Z | state_transition | EXECUTING | REPLAN | reason=SOURCE_DRIFT; failure_class=SOURCE_DRIFT |
| 57897 | 2026-09-15T07:40:01.518Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `157`
- Chain head: `9f60fdae5283de9c93f97921c9edbdd993758d31b935a527da1eeff6f051481f`
