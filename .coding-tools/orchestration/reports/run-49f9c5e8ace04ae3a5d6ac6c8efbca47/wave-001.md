# Orchestration Wave 1

- Run: `49f9c5e8ace04ae3a5d6ac6c8efbca47`
- Wave: `6b466b04b5724fa29c1473d97fa5e05c`
- Objective: Fix the proven structured-process safety defect in crates/webcodex-core/src/shell_protocol.rs only. process_uses_shell_command_mode must reject the explicit command-text modes cmd.exe /K and PowerShell/pwsh -EncodedCommand in addition to the modes it already rejects. Extend the existing validate_process_argv shell-command-mode regression with exact /K and -EncodedCommand cases. Do not add speculative abbreviations or reject unrelated options. Keep P5 closed.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `95a5f650b31f8bace44966d9439235ec229f09129ad06a72c643c15039e13359`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18565 | 2026-08-18T23:45:28.237Z | run_started |  | PREFLIGHT |  |
| 18566 | 2026-08-18T23:45:33.369Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18567 | 2026-08-18T23:45:49.282Z | solution_shadow_recommended |  |  |  |
| 18568 | 2026-08-18T23:46:17.903Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 18569 | 2026-08-18T23:46:18.070Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 18570 | 2026-08-18T23:46:18.221Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 18571 | 2026-08-18T23:46:18.338Z | state_transition | READY | ROUTED | reason=route_selected |
| 18572 | 2026-08-18T23:46:18.790Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3d40e39edf5742138683df600dc96a47 |
| 18573 | 2026-08-18T23:46:18.937Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 18574 | 2026-08-18T23:46:19.371Z | solution_shadow_patch_surface_observed |  |  |  |
| 18575 | 2026-08-18T23:46:19.572Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3d40e39edf5742138683df600dc96a47 |
| 18576 | 2026-08-18T23:46:19.686Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 18577 | 2026-08-18T23:46:20.032Z | proof_cache_miss |  |  | reason=cold; stage_id=check:de564d136649765f; input_fingerprint=ac13f19bb4d55457fa79b539b3322f2f6eab47a8f36c13933102f8fdb287221c |
| 18578 | 2026-08-18T23:46:20.354Z | managed_process_admitted |  |  | owner=default |
| 18579 | 2026-08-18T23:46:20.562Z | managed_process_started |  |  | owner=default |
| 18580 | 2026-08-18T23:46:20.954Z | managed_process_terminal |  |  | owner=default |
| 18581 | 2026-08-18T23:46:21.213Z | proof_recorded |  |  | stage_id=check:de564d136649765f; status=failed; cache_hit=False; input_fingerprint=ac13f19bb4d55457fa79b539b3322f2f6eab47a8f36c13933102f8fdb287221c |
| 18582 | 2026-08-18T23:46:21.321Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 18583 | 2026-08-18T23:46:21.463Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 18584 | 2026-08-18T23:46:21.593Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:de564d136649765f | failed | ac13f19bb4d55457fa79b539b3322f2f6eab47a8f36c13933102f8fdb287221c | False | 907 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `2abdba7870ddf013092c5fb47b9b5de59d78f9b41f43fb9640b2a52a3a8e4448`
