# Orchestration Wave 1

- Run: `ee62554e999645169a35f64864c8dbf0`
- Wave: `6a3ff0716ef84e99b97569c1fbc1b2ba`
- Objective: Apply the smallest lifecycle fix for the active mcp_only RUN/WAVE: AcceptedCodeActivationController must not start while a durable full-clean epoch is VERIFYING/FAILED/expired or READY-but-blocked, but RecoveryHost supervision must idempotently arm it as soon as the same durable epoch becomes READY with admission OPEN after bootstrap/finalize. Preserve bootstrap and ready-adoption authority guards. Do not create connector/discovery receipts, use raw HTTP/direct SQLite/force release, restart runtime, commit, push, deploy, or broaden scope.
- Objective revision: `1`
- Objective SHA-256: `55faf10dc33e889f9941d148abf0ec2ecdc3284960b8912b7528022050f1a15b`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a357e1bb45a68cfaf25b8a2aa99a133ab256102c`
- Worktree fingerprint: `81cb90a3d72b73bb626b3d8ff235009f13f70d5c020652a204fd6b50def4dbc1`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32827 | 2026-08-30T20:15:31.984Z | run_started |  | PREFLIGHT |  |
| 32828 | 2026-08-30T20:15:32.641Z | observation_span_recorded |  |  |  |
| 32829 | 2026-08-30T20:16:09.853Z | solution_shadow_recommended |  |  |  |
| 32830 | 2026-08-30T20:16:10.102Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32831 | 2026-08-30T20:16:10.300Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32832 | 2026-08-30T20:16:10.658Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 32833 | 2026-08-30T20:16:10.873Z | state_transition | READY | ROUTED | reason=route_selected |
| 32834 | 2026-08-30T20:16:11.078Z | observation_span_recorded |  |  |  |
| 32835 | 2026-08-30T20:16:11.913Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cbeec500a17b4e1c8c0aa633027ffbaa |
| 32836 | 2026-08-30T20:16:12.157Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32837 | 2026-08-30T20:16:12.933Z | patch_surface_observed |  |  |  |
| 32838 | 2026-08-30T20:16:13.114Z | observation_span_recorded |  |  |  |
| 32839 | 2026-08-30T20:16:13.398Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cbeec500a17b4e1c8c0aa633027ffbaa |
| 32840 | 2026-08-30T20:16:13.597Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32841 | 2026-08-30T20:16:14.256Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=53910c7b66be5f4e790857960b5c5324fe63a6990269e5469de00b5b2c569e44 |
| 32842 | 2026-08-30T20:16:14.688Z | managed_process_admitted |  |  | owner=default |
| 32843 | 2026-08-30T20:16:15.005Z | managed_process_started |  |  | owner=default |
| 32844 | 2026-08-30T20:16:48.063Z | managed_process_terminal |  |  | owner=default |
| 32845 | 2026-08-30T20:16:48.470Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=53910c7b66be5f4e790857960b5c5324fe63a6990269e5469de00b5b2c569e44 |
| 32846 | 2026-08-30T20:16:49.043Z | observation_span_recorded |  |  |  |
| 32847 | 2026-08-30T20:16:49.242Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 32848 | 2026-08-30T20:16:49.446Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 32849 | 2026-08-30T20:16:49.664Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 53910c7b66be5f4e790857960b5c5324fe63a6990269e5469de00b5b2c569e44 | False | 33735 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `96`
- Chain head: `bc31868acd8777955479f2e126e7679db7e39db2513ec563fcbd58423293e6fb`
