# Orchestration Wave 1

- Run: `57b2fa22fa444425bf6109a904a68456`
- Wave: `16a897a7fa1c4f709a880b643eb74436`
- Objective: Fix the proven deferred-observer race only in scripts/full-clean-activation.js: when waitForReplacementReady has already matched the exact replacement descriptor epoch, exact status epoch, and exact operation_id, but runtime.lightweight_snapshot transiently reports a prior activation epoch from the Recovery Host supervision cache, classify only that runtime-snapshot epoch mismatch as retryable ACTIVATION_HANDOFF_PENDING so the existing catch/poll loop waits. Preserve fail-closed descriptor/status/operation mismatch checks and require the runtime snapshot epoch to match exactly before READY. Add one focused regression in tests/full-clean-activation-command.test.js where the first lightweight snapshot reports a prior epoch, the next reports the exact epoch, and readiness returns only after the exact snapshot without terminal ACTIVATION_OPERATION_MISMATCH. Preserve all unrelated dirty WIP and do not touch .coding-tools manually or protected foreign lineage.
- Objective revision: `1`
- Objective SHA-256: `4ffa4db7232f6395e6fb5abc00b10d12539eb923c6925978fd9cefad3db27116`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `912c83a7e33884ac662c884c190d689cb778718779a24f26a4afbf59bed3efae`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44690 | 2026-09-08T20:45:47.600Z | run_started |  | PREFLIGHT |  |
| 44691 | 2026-09-08T20:45:48.003Z | observation_span_recorded |  |  |  |
| 44692 | 2026-09-08T20:45:48.288Z | solution_shadow_recommended |  |  |  |
| 44693 | 2026-09-08T20:45:53.872Z | observation_span_recorded |  |  |  |
| 44694 | 2026-09-08T20:45:54.084Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 44695 | 2026-09-08T20:46:55.015Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44696 | 2026-09-08T20:46:55.258Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44697 | 2026-09-08T20:46:55.472Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 44698 | 2026-09-08T20:46:55.661Z | state_transition | READY | ROUTED | reason=route_selected |
| 44699 | 2026-09-08T20:46:55.894Z | observation_span_recorded |  |  |  |
| 44700 | 2026-09-08T20:46:56.687Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ed83b8c4d03b4481adbb373b2589d793 |
| 44701 | 2026-09-08T20:46:56.868Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44702 | 2026-09-08T20:46:57.701Z | patch_surface_observed |  |  |  |
| 44703 | 2026-09-08T20:46:57.970Z | observation_span_recorded |  |  |  |
| 44704 | 2026-09-08T20:46:58.311Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ed83b8c4d03b4481adbb373b2589d793 |
| 44705 | 2026-09-08T20:46:58.520Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44706 | 2026-09-08T20:46:59.313Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bcb9533c87e955fe; input_fingerprint=6afa576c6c965b3dd6ef6b0d31a2923a43562a9893a1ff986af004ae953f1b90 |
| 44707 | 2026-09-08T20:46:59.781Z | managed_process_admitted |  |  | owner=default |
| 44708 | 2026-09-08T20:47:00.375Z | managed_process_started |  |  | owner=default |
| 44709 | 2026-09-08T20:47:03.247Z | managed_process_terminal |  |  | owner=default |
| 44710 | 2026-09-08T20:47:03.667Z | proof_recorded |  |  | stage_id=check:bcb9533c87e955fe; status=passed; cache_hit=False; input_fingerprint=6afa576c6c965b3dd6ef6b0d31a2923a43562a9893a1ff986af004ae953f1b90 |
| 44711 | 2026-09-08T20:47:03.881Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:23efc2d04b2baee1; input_fingerprint=1b0040f2aefcfc98ed36224fe2e4dfb9648c991cc95d66163d2eada1dd5c88ed |
| 44712 | 2026-09-08T20:47:04.328Z | managed_process_admitted |  |  | owner=default |
| 44713 | 2026-09-08T20:47:04.706Z | managed_process_started |  |  | owner=default |
| 44714 | 2026-09-08T20:47:05.207Z | managed_process_terminal |  |  | owner=default |
| 44715 | 2026-09-08T20:47:05.611Z | proof_recorded |  |  | stage_id=check:23efc2d04b2baee1; status=passed; cache_hit=False; input_fingerprint=1b0040f2aefcfc98ed36224fe2e4dfb9648c991cc95d66163d2eada1dd5c88ed |
| 44716 | 2026-09-08T20:47:06.511Z | observation_span_recorded |  |  |  |
| 44717 | 2026-09-08T20:47:06.731Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44718 | 2026-09-08T20:48:24.462Z | managed_process_admitted |  |  | owner=default |
| 44719 | 2026-09-08T20:48:24.828Z | managed_process_started |  |  | owner=default |
| 44720 | 2026-09-08T20:48:25.342Z | managed_process_terminal |  |  | owner=default |
| 44721 | 2026-09-08T20:48:40.161Z | managed_process_admitted |  |  | owner=default |
| 44722 | 2026-09-08T20:48:40.561Z | managed_process_started |  |  | owner=default |
| 44723 | 2026-09-08T20:48:41.102Z | managed_process_terminal |  |  | owner=default |
| 44724 | 2026-09-08T20:48:49.835Z | managed_process_admitted |  |  | owner=default |
| 44725 | 2026-09-08T20:48:50.175Z | managed_process_started |  |  | owner=default |
| 44726 | 2026-09-08T20:48:50.709Z | managed_process_terminal |  |  | owner=default |
| 44727 | 2026-09-08T20:48:58.200Z | managed_process_admitted |  |  | owner=default |
| 44728 | 2026-09-08T20:48:58.541Z | managed_process_started |  |  | owner=default |
| 44729 | 2026-09-08T20:48:59.043Z | managed_process_terminal |  |  | owner=default |
| 44730 | 2026-09-08T20:50:34.675Z | quality_outcome_recorded |  |  |  |
| 44731 | 2026-09-08T20:50:34.889Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44732 | 2026-09-08T20:50:35.189Z | observation_span_recorded |  |  |  |
| 44733 | 2026-09-08T20:50:35.412Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:bcb9533c87e955fe | passed | 6afa576c6c965b3dd6ef6b0d31a2923a43562a9893a1ff986af004ae953f1b90 | False | 3971 | 0 |
| check:23efc2d04b2baee1 | passed | 1b0040f2aefcfc98ed36224fe2e4dfb9648c991cc95d66163d2eada1dd5c88ed | False | 1387 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 8d3bc91d6f4e49aca30a15fdd63a4f0c | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | ee0cbb46abc9dbbffb4b3d1c061098c4eade7a08ca2f87104d4c7da01b72e628 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `3293d8f2b052abec6786e9300f35c8841838daffdab2c89b487b6df7ab79dcac`
