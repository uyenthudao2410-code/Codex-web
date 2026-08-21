# Orchestration Wave 2

- Run: `bbdb7fbc326c41be92245af9a521180f`
- Wave: `83c383e819344edeb2c8dd41a7bc5d23`
- Objective: Prepare the final exact-fingerprint engineering RC closure for the current authoritative worktree after accepted P0.3. Identify the maintained repository commands/tests for: full npm tests, full coding-tools-mcp pytest, Recovery E2E, packaged Recovery verification, OpenCode preflight, npm audit, final npm dist build, installer/hash/provenance verification, and final source-bundle/private-runtime-state guards. Do not mutate source/docs, do not reuse stale dist as final proof, do not commit/push/restart/deploy/release/tag/publish. Preserve all .coding-tools evidence and the active resident codex-app-server.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `a583d186f91ae78e578059f61afe109b09e82f5b514f628d681a967a63910252`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25689 | 2026-08-21T03:58:10.206Z | wave_replanned |  | PREFLIGHT | reason=Full MCP RC proof exposed five concrete failures; inspect exact shared root cause before any mutation instead of retrying unchanged evidence. |
| 25690 | 2026-08-21T03:58:11.115Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25691 | 2026-08-21T03:58:34.389Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25692 | 2026-08-21T03:59:39.227Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25693 | 2026-08-21T03:59:59.177Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25694 | 2026-08-21T04:00:53.584Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25695 | 2026-08-21T04:01:07.215Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25696 | 2026-08-21T04:02:07.184Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25697 | 2026-08-21T04:02:21.321Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 25698 | 2026-08-21T04:06:02.925Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25699 | 2026-08-21T04:06:03.101Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25700 | 2026-08-21T04:06:03.322Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 25701 | 2026-08-21T04:06:03.485Z | state_transition | READY | ROUTED | reason=route_selected |
| 25702 | 2026-08-21T04:06:04.106Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e73bd6f83ba54014bd8d9e4c271492c0 |
| 25703 | 2026-08-21T04:06:04.278Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25704 | 2026-08-21T04:06:04.663Z | patch_surface_observed |  |  |  |
| 25705 | 2026-08-21T04:06:04.855Z | patch_surface_observed |  |  |  |
| 25706 | 2026-08-21T04:06:05.066Z | patch_surface_observed |  |  |  |
| 25707 | 2026-08-21T04:06:05.285Z | patch_surface_observed |  |  |  |
| 25708 | 2026-08-21T04:06:05.470Z | patch_surface_observed |  |  |  |
| 25709 | 2026-08-21T04:06:05.649Z | patch_surface_observed |  |  |  |
| 25710 | 2026-08-21T04:06:05.869Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e73bd6f83ba54014bd8d9e4c271492c0 |
| 25711 | 2026-08-21T04:06:06.007Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25712 | 2026-08-21T04:06:06.380Z | proof_cache_miss |  |  | reason=cold; stage_id=check:63ae3dafa4553097; input_fingerprint=c3698cd6790831f841091a0919ac5d90a33b23948028db5f6d853ad7604f9b24 |
| 25713 | 2026-08-21T04:06:06.724Z | managed_process_admitted |  |  | owner=default |
| 25714 | 2026-08-21T04:06:07.015Z | managed_process_started |  |  | owner=default |
| 25715 | 2026-08-21T04:06:38.015Z | managed_process_terminal |  |  | owner=default |
| 25716 | 2026-08-21T04:06:38.372Z | proof_recorded |  |  | stage_id=check:63ae3dafa4553097; status=failed; cache_hit=False; input_fingerprint=c3698cd6790831f841091a0919ac5d90a33b23948028db5f6d853ad7604f9b24 |
| 25717 | 2026-08-21T04:06:38.540Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 25718 | 2026-08-21T04:06:38.702Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 25719 | 2026-08-21T04:06:38.918Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:63ae3dafa4553097 | failed | c3698cd6790831f841091a0919ac5d90a33b23948028db5f6d853ad7604f9b24 | False | 31693 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `83`
- Chain head: `068e059d393817492479ccfa6a38b5ba37e372453fe1bb6926cc4f46fc3bfdec`
