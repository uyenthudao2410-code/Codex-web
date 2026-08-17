# Orchestration Wave 1

- Run: `1151d304b5864708ad6f694d9fd91b6c`
- Wave: `0155151d6cd74afa94a1115460aa3b44`
- Objective: Execute P0.2 installed Windows Recovery Supervisor current-session acceptance only on the controlled acceptance installation. Exact source HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117; exact installer SHA-256 0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879; expected installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420. Immutable before-state Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Replace only %LOCALAPPDATA%\WebMcpAcceptance-0.3.4, install the same-user Limited WebMCP Recovery Supervisor Scheduled Task from the installed package, prove continuous healthy with the exact same Recovery Host, stop task and prove installed Action Once observes the same host with no spawn, restart and re-prove continuous healthy, prove listener/device coherence, then uninstall the Scheduled Task/supervisor and prove rollback. Never kill or replace the active development Recovery Host/MCP/Tunnel. Do not infer reboot/logon persistence. No source changes and no rebuild.
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
| 12696 | 2026-08-17T08:43:43.292Z | run_started |  | PREFLIGHT |  |
| 12697 | 2026-08-17T08:43:43.700Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12698 | 2026-08-17T08:43:43.826Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12699 | 2026-08-17T08:43:43.933Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12700 | 2026-08-17T08:43:44.098Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12701 | 2026-08-17T08:43:44.245Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12702 | 2026-08-17T08:43:44.367Z | state_transition | READY | ROUTED | reason=route_selected |
| 12703 | 2026-08-17T08:43:44.746Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ed3ed61c8e3f4a5bad2e77b76c496f8a |
| 12704 | 2026-08-17T08:43:44.912Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12705 | 2026-08-17T08:43:45.328Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ed3ed61c8e3f4a5bad2e77b76c496f8a |
| 12706 | 2026-08-17T08:43:45.462Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12707 | 2026-08-17T08:43:45.783Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e5b371de479d5dc0; input_fingerprint=8e7b4bf048dadbb1fbbdb09c8e2f9053674f0d932ad4f0b8e319fc5c7b3fbb22 |
| 12708 | 2026-08-17T08:43:46.062Z | managed_process_admitted |  |  | owner=default |
| 12709 | 2026-08-17T08:43:46.279Z | managed_process_started |  |  | owner=default |
| 12710 | 2026-08-17T08:44:20.285Z | managed_process_terminal |  |  | owner=default |
| 12711 | 2026-08-17T08:44:20.610Z | proof_recorded |  |  | stage_id=check:e5b371de479d5dc0; status=failed; cache_hit=False; input_fingerprint=8e7b4bf048dadbb1fbbdb09c8e2f9053674f0d932ad4f0b8e319fc5c7b3fbb22 |
| 12712 | 2026-08-17T08:44:20.784Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 12713 | 2026-08-17T08:44:20.947Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 12714 | 2026-08-17T08:44:21.061Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e5b371de479d5dc0 | failed | 8e7b4bf048dadbb1fbbdb09c8e2f9053674f0d932ad4f0b8e319fc5c7b3fbb22 | False | 34487 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `fd740e375db743295902c880e2a0c98584398a7287444f946ff9e9168d34c37f`
