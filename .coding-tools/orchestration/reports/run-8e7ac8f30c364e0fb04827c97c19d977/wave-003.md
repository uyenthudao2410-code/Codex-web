# Orchestration Wave 3

- Run: `8e7ac8f30c364e0fb04827c97c19d977`
- Wave: `aa84f7a11b45449582e7d21781785a40`
- Objective: Implement only the source-and-focused-test portion of the proven C01 Recovery Supervisor host-visibility fix for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Move installed supervisor bytes to %APPDATA%\web-mcp-assistant\recovery-supervisor, retain the old LocalApplicationData root only for legacy migration cleanup, signal the legacy stop sentinel during replacement when present, clean the legacy root only after a fresh valid new-root heartbeat, and clean both roots on uninstall. Keep the direct hidden Windows PowerShell Scheduled Task action unchanged. Add focused static contract coverage. Documentation is intentionally deferred to the next wave to minimize the EOCL mutation window after the prior SOURCE_DRIFT. Do not install supervisor, restart runtime, build, reboot, commit, push, release, or deploy.
- Objective revision: `3`
- Objective SHA-256: `75a1db979fad03349553bb34f48e68b741bce87775945df95520a4e7702515fe`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `5f08d87d05f841d3b7921ca5d6106f0e420d2323cdfa42694bec46d593a82a9b`
- Contract fingerprint: `64adc198e7bde4c96465dc6929f6402e4c55ea8179f1a307417f03fc4568e7ea`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 57905 | 2026-09-15T07:41:19.791Z | wave_replanned |  | PREFLIGHT | reason=The prior mutation wave hit SOURCE_DRIFT while another command was active. Control-plane now reports quiescent=true and modified_files=[] for the failed wave. This replan narrows the mutation surface from 3 files to source+focused test only; documentation is deferred until the code checkpoint is accepted. |
| 57906 | 2026-09-15T07:41:20.402Z | observation_span_recorded |  |  |  |
| 57907 | 2026-09-15T07:41:21.244Z | observation_span_recorded |  |  |  |
| 57908 | 2026-09-15T07:41:21.438Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 57909 | 2026-09-15T07:41:21.823Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 57910 | 2026-09-15T07:41:22.220Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 57911 | 2026-09-15T07:41:22.538Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 57912 | 2026-09-15T07:41:22.849Z | state_transition | READY | ROUTED | reason=route_selected |
| 57913 | 2026-09-15T07:41:23.263Z | observation_span_recorded |  |  |  |
| 57914 | 2026-09-15T07:41:24.375Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9da40a4445904fb1a5fc4596af99b420 |
| 57915 | 2026-09-15T07:41:24.737Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 57916 | 2026-09-15T07:41:25.607Z | patch_surface_observed |  |  |  |
| 57917 | 2026-09-15T07:41:26.014Z | observation_span_recorded |  |  |  |
| 57918 | 2026-09-15T07:41:26.480Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9da40a4445904fb1a5fc4596af99b420 |
| 57919 | 2026-09-15T07:41:26.699Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 57920 | 2026-09-15T07:41:27.739Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:387c4d3f79f45a91; input_fingerprint=c3768a0532717d74ecb55ba498ee2b9bd46c35145af40b97b7b1acd57e25e684 |
| 57921 | 2026-09-15T07:41:28.763Z | managed_process_admitted |  |  | owner=default |
| 57922 | 2026-09-15T07:41:29.342Z | managed_process_started |  |  | owner=default |
| 57925 | 2026-09-15T07:42:00.351Z | managed_process_terminal |  |  | owner=default |
| 57926 | 2026-09-15T07:42:00.813Z | proof_recorded |  |  | stage_id=check:387c4d3f79f45a91; status=failed; cache_hit=False; input_fingerprint=c3768a0532717d74ecb55ba498ee2b9bd46c35145af40b97b7b1acd57e25e684 |
| 57927 | 2026-09-15T07:42:01.051Z | observation_span_recorded |  |  |  |
| 57928 | 2026-09-15T07:42:01.367Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 57929 | 2026-09-15T07:42:01.562Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 57930 | 2026-09-15T07:42:01.833Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 57974 | 2026-09-15T07:43:56.877Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:387c4d3f79f45a91 | failed | c3768a0532717d74ecb55ba498ee2b9bd46c35145af40b97b7b1acd57e25e684 | False | 32437 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `9f60fdae5283de9c93f97921c9edbdd993758d31b935a527da1eeff6f051481f`
