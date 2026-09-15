# Orchestration Wave 3

- Run: `fc572e1f8aac4f179545241679faf8b6`
- Wave: `d0e4ca58f710442c9c5509b561b9fdd8`
- Objective: Replan the same C01/M02 pre-reboot engineering attempt after Wave 2 reached NSIS installation but failed the custom InstallLocation-based registry assertion. Gather the repository-owned uninstall-registration semantics from scripts/installed-recovery-smoke.js and verify the rollback state is clean before any further mutation: %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 must be absent or clearly characterized, no matching live uninstall registration for that acceptance root may remain, and the production development Recovery Host plus development supervisor task/manifest identity must still be intact. Determine why electron-builder NSIS registration was not counted by InstallLocation and derive the exact repo-consistent predicate for the next wave. This is PREPARE only: do not install/uninstall anything, change registry/tasks/stop.request, restart runtime, reboot/logoff, edit source, clear state, commit, push, publish, release, or deploy.
- Objective revision: `3`
- Objective SHA-256: `44c3ca2c62140a95aa6db3d699bddf14367ce75f503efa8307a4695dadb78a1e`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `eca6ac884dc99ec50502c2fda69e5c85cba60db367cfcbb4b9298f94b5aa66b1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 56994 | 2026-09-15T06:43:16.211Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 fixed malformed registry-entry handling and successfully invoked NSIS, but the custom post-install predicate incorrectly required exactly one uninstall row whose InstallLocation normalized to the target. The repository-owned installed-recovery-smoke already proved registration behavior with different semantics. The next strategy first reads and adopts that authoritative predicate and verifies rollback cleanliness before any new installer side effect. |
| 56995 | 2026-09-15T06:43:16.510Z | observation_span_recorded |  |  |  |
| 57001 | 2026-09-15T06:43:22.567Z | observation_span_recorded |  |  |  |
| 57002 | 2026-09-15T06:43:22.815Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57005 | 2026-09-15T06:43:50.203Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57006 | 2026-09-15T06:43:50.424Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57007 | 2026-09-15T06:43:50.623Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 57008 | 2026-09-15T06:43:50.881Z | state_transition | READY | ROUTED | reason=route_selected |
| 57009 | 2026-09-15T06:43:51.125Z | observation_span_recorded |  |  |  |
| 57010 | 2026-09-15T06:43:51.774Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=847ecb3f9e4c4141924ba915c31a1994 |
| 57011 | 2026-09-15T06:43:51.982Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57012 | 2026-09-15T06:43:52.527Z | observation_span_recorded |  |  |  |
| 57013 | 2026-09-15T06:43:52.831Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=847ecb3f9e4c4141924ba915c31a1994 |
| 57014 | 2026-09-15T06:43:53.003Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57015 | 2026-09-15T06:43:53.612Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7ab1f33ccf3e959f; input_fingerprint=cfd9937ad9389dd1b09fc76293a108b107a7a21eedf71d257344dc3d4cee85e7 |
| 57016 | 2026-09-15T06:43:54.048Z | managed_process_admitted |  |  | owner=default |
| 57017 | 2026-09-15T06:43:54.375Z | managed_process_started |  |  | owner=default |
| 57018 | 2026-09-15T06:44:11.047Z | managed_process_terminal |  |  | owner=default |
| 57019 | 2026-09-15T06:44:11.444Z | proof_recorded |  |  | stage_id=check:7ab1f33ccf3e959f; status=passed; cache_hit=False; input_fingerprint=cfd9937ad9389dd1b09fc76293a108b107a7a21eedf71d257344dc3d4cee85e7 |
| 57020 | 2026-09-15T06:44:11.730Z | observation_span_recorded |  |  |  |
| 57021 | 2026-09-15T06:44:11.959Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 57022 | 2026-09-15T06:44:12.163Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 57025 | 2026-09-15T06:44:28.365Z | quality_outcome_recorded |  |  |  |
| 57026 | 2026-09-15T06:44:28.607Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 57027 | 2026-09-15T06:44:29.025Z | observation_span_recorded |  |  |  |
| 57028 | 2026-09-15T06:44:29.293Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 57029 | 2026-09-15T06:44:29.562Z | observation_span_recorded |  |  |  |
| 57030 | 2026-09-15T06:44:29.825Z | observation_span_recorded |  |  |  |
| 57031 | 2026-09-15T06:44:30.080Z | continuity_telemetry_recorded |  |  |  |
| 57032 | 2026-09-15T06:45:54.313Z | continuity_telemetry_recorded |  |  |  |
| 57033 | 2026-09-15T06:45:54.595Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7ab1f33ccf3e959f | passed | cfd9937ad9389dd1b09fc76293a108b107a7a21eedf71d257344dc3d4cee85e7 | False | 17472 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 53f2b9a5e4494769b5b93e8f4f72f028 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 2680ba96d109d3631595027a18490558e5fd72b232d285d4278aa4a6a7e369da | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `0c006a821b788c3fd064513531d1376fb7117c3732b8af155ab03e9518736245`
