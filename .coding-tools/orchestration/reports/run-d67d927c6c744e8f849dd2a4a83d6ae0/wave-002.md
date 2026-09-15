# Orchestration Wave 2

- Run: `d67d927c6c744e8f849dd2a4a83d6ae0`
- Wave: `232640f21b2a40d3a457bd6b9e02474a`
- Objective: Replanned isolated installed-smoke phase for canonical Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Validate accepted NSIS candidate dist/coding-tools-mcp-setup-1.0.0.exe SHA256 8597162DB4D2E3D0955FD8F123F70DA543C79475B17EFAD4DDB088F289429F8E with repository-owned node scripts/installed-recovery-smoke.js. Current HKCU inspection proves zero existing Coding Tools MCP user installs, so this wave must not create a persistent install. The harness may create only its temporary NSIS install, must run packaged recovery smoke, uninstall it, and must prove production recovery descriptor plus WebMCP Recovery Supervisor Scheduled Task stay unchanged. Do not edit source, stop/restart the development runtime, reboot, clear/reset state, commit, push, publish, release, or deploy.
- Objective revision: `2`
- Objective SHA-256: `4dc2ac41c26a80027ac7726072856062b02d74496b6f19ec2497e5badbfba385`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `0d2cb6a5071937d5a826532d2ffc651c7e09691359db78898912a7926917112c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 56848 | 2026-09-15T06:31:09.615Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 entered BASE_DRIFT after read-only preflight/registry inspection changed control-plane evidence. It made no source changes and ran no proof. New evidence materially narrows strategy: HKCU contains zero Coding Tools MCP user installs, so replace-stale-install is inapplicable. Run the repository-owned isolated temporary install/uninstall smoke instead and require production descriptor/task stability. |
| 56849 | 2026-09-15T06:31:10.427Z | observation_span_recorded |  |  |  |
| 56850 | 2026-09-15T06:31:15.938Z | observation_span_recorded |  |  |  |
| 56851 | 2026-09-15T06:31:16.135Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 56852 | 2026-09-15T06:31:16.324Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 56853 | 2026-09-15T06:31:16.507Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 56854 | 2026-09-15T06:31:16.698Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 56855 | 2026-09-15T06:31:16.885Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 56856 | 2026-09-15T06:31:17.298Z | state_transition | READY | ROUTED | reason=route_selected |
| 56857 | 2026-09-15T06:31:17.636Z | observation_span_recorded |  |  |  |
| 56858 | 2026-09-15T06:31:18.406Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=16522b9cb39e48e4a69c840d2998e1f2 |
| 56859 | 2026-09-15T06:31:18.662Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 56860 | 2026-09-15T06:31:19.308Z | observation_span_recorded |  |  |  |
| 56861 | 2026-09-15T06:31:19.750Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=16522b9cb39e48e4a69c840d2998e1f2 |
| 56862 | 2026-09-15T06:31:19.982Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 56863 | 2026-09-15T06:31:20.470Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bda80ff0a48cc0e7; input_fingerprint=b9d552ac456b081f679f56565e4558f6555a005992423eec7a52c306317ea641 |
| 56864 | 2026-09-15T06:31:21.000Z | managed_process_admitted |  |  | owner=default |
| 56865 | 2026-09-15T06:31:21.405Z | managed_process_started |  |  | owner=default |
| 56887 | 2026-09-15T06:32:32.868Z | managed_process_terminal |  |  | owner=default |
| 56888 | 2026-09-15T06:32:33.780Z | proof_recorded |  |  | stage_id=check:bda80ff0a48cc0e7; status=passed; cache_hit=False; input_fingerprint=b9d552ac456b081f679f56565e4558f6555a005992423eec7a52c306317ea641 |
| 56889 | 2026-09-15T06:32:34.475Z | observation_span_recorded |  |  |  |
| 56890 | 2026-09-15T06:32:35.105Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 56891 | 2026-09-15T06:32:35.947Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 56897 | 2026-09-15T06:33:42.617Z | quality_outcome_recorded |  |  |  |
| 56898 | 2026-09-15T06:33:43.080Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 56899 | 2026-09-15T06:33:43.634Z | observation_span_recorded |  |  |  |
| 56900 | 2026-09-15T06:33:44.511Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 56901 | 2026-09-15T06:33:44.980Z | observation_span_recorded |  |  |  |
| 56902 | 2026-09-15T06:33:45.705Z | observation_span_recorded |  |  |  |
| 56903 | 2026-09-15T06:33:46.328Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:bda80ff0a48cc0e7 | passed | b9d552ac456b081f679f56565e4558f6555a005992423eec7a52c306317ea641 | False | 72434 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 577b890ebdfe487d8ca99f95df333af8 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 7b7daa3347eb3bc07e25a4d7debf305d9570366607d9115f4fe916b0fad0c657 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `3126b76392e2fb410f6cdb1ca921ce3afd812143bc6a51a013c001a4bc5b73c8`
