# Orchestration Wave 1

- Run: `64fb291f72f04dbcb43da4ccaaa4bfef`
- Wave: `3ed2ca8e2596421c8c827fce65b73c78`
- Objective: Fix EOCL task/run projection isolation only. A task that already has its own task_id must never adopt a workspace-global active orchestration run that belongs to a different task_id. In _reconcile_task_orchestration_projection, first resolve an active run by the current task_id; permit legacy workspace-global fallback only when the current task truly has no task_id. Add a focused regression proving task_id B with no projection does not attach to active run task_id A. Preserve the accepted completion-report ACK repair and all unrelated dirty changes. Explicitly exclude resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py and resources/coding-tools-mcp/tests/test_truth_snapshot.py. No restart, commit, push, package, release, deploy, T3 or C1.
- Objective revision: `1`
- Objective SHA-256: `36b60d59fbc2986082396c37006678ece15ab4117341f3b68d95e54979e7bd06`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `347eecd98099ff8c30c466aa94e4c130b0464eefdffea3a54ee15405f48b6d9e`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26340 | 2026-08-21T20:35:46.865Z | run_started |  | PREFLIGHT |  |
| 26341 | 2026-08-21T20:35:47.712Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26342 | 2026-08-21T20:36:47.085Z | managed_process_admitted |  |  | owner=default |
| 26343 | 2026-08-21T20:36:47.365Z | managed_process_started |  |  | owner=default |
| 26344 | 2026-08-21T20:36:47.925Z | managed_process_terminal |  |  | owner=default |
| 26345 | 2026-08-21T20:36:59.915Z | managed_process_admitted |  |  | owner=default |
| 26346 | 2026-08-21T20:37:00.192Z | managed_process_started |  |  | owner=default |
| 26347 | 2026-08-21T20:37:00.600Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 26348 | 2026-08-21T20:37:22.244Z | managed_process_admitted |  |  | owner=default |
| 26349 | 2026-08-21T20:37:22.590Z | managed_process_started |  |  | owner=default |
| 26350 | 2026-08-21T20:37:23.023Z | managed_process_terminal |  |  | owner=default |
| 26351 | 2026-08-21T20:37:55.342Z | solution_shadow_recommended |  |  |  |
| 26352 | 2026-08-21T20:38:10.158Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26353 | 2026-08-21T20:38:10.331Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26354 | 2026-08-21T20:38:10.473Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26355 | 2026-08-21T20:38:10.715Z | state_transition | READY | ROUTED | reason=route_selected |
| 26356 | 2026-08-21T20:38:11.155Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f95dbd165e5e497ca1736dda43fd39b2 |
| 26357 | 2026-08-21T20:38:11.322Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26358 | 2026-08-21T20:38:11.754Z | patch_surface_observed |  |  |  |
| 26359 | 2026-08-21T20:38:12.022Z | patch_surface_observed |  |  |  |
| 26360 | 2026-08-21T20:38:12.317Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f95dbd165e5e497ca1736dda43fd39b2 |
| 26361 | 2026-08-21T20:38:12.488Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26362 | 2026-08-21T20:38:12.833Z | proof_cache_miss |  |  | reason=cold; stage_id=check:781a4fe621629a53; input_fingerprint=cd9b7516d03d4810c194acad8f2b658384e420f64fa36305cd0fb4f8f6333652 |
| 26363 | 2026-08-21T20:38:13.194Z | managed_process_admitted |  |  | owner=default |
| 26364 | 2026-08-21T20:38:13.619Z | managed_process_started |  |  | owner=default |
| 26365 | 2026-08-21T20:38:14.037Z | managed_process_terminal |  |  | owner=default |
| 26366 | 2026-08-21T20:38:14.431Z | proof_recorded |  |  | stage_id=check:781a4fe621629a53; status=failed; cache_hit=False; input_fingerprint=cd9b7516d03d4810c194acad8f2b658384e420f64fa36305cd0fb4f8f6333652 |
| 26367 | 2026-08-21T20:38:14.607Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 26368 | 2026-08-21T20:38:14.787Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 26369 | 2026-08-21T20:38:15.015Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:781a4fe621629a53 | failed | cd9b7516d03d4810c194acad8f2b658384e420f64fa36305cd0fb4f8f6333652 | False | 1222 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `ac7f647355424060b530b16aa6183158621a38c9729fc9936df8eecebe0592c9`
