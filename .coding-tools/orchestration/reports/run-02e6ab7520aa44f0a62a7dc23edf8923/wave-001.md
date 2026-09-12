# Orchestration Wave 1

- Run: `02e6ab7520aa44f0a62a7dc23edf8923`
- Wave: `61f6aa46f29044498b67330d1546190c`
- Objective: Fix the proven deferred-observer defect only in scripts/full-clean-activation.js: in waitForReplacementOperation, recover from missing ephemeral code.activation_status only when the durable bootstrap result is completed and its exact operation/epoch agrees with replacement descriptor epoch, projected status epoch, and observed status operation ID. Reuse the bootstrapResult object as operation. Preserve failed/expired UPDATE_INCOMPLETE, pending polling, and all mismatch guards. Add the focused regression in tests/full-clean-activation-command.test.js. Preserve all unrelated WIP.
- Objective revision: `1`
- Objective SHA-256: `5029db31b985e80c6a179e2ccedca59392c244a9eba581d004e97b65c2bed3e7`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `aec9468f04470a22668a8be642645928b652c030f3873d82fe9774ea5c3690a3`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44739 | 2026-09-08T21:01:03.870Z | run_started |  | PREFLIGHT |  |
| 44740 | 2026-09-08T21:01:04.331Z | observation_span_recorded |  |  |  |
| 44741 | 2026-09-08T21:01:04.575Z | solution_shadow_recommended |  |  |  |
| 44742 | 2026-09-08T21:01:04.797Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44743 | 2026-09-08T21:01:04.997Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44744 | 2026-09-08T21:01:05.208Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 44745 | 2026-09-08T21:01:05.374Z | state_transition | READY | ROUTED | reason=route_selected |
| 44746 | 2026-09-08T21:01:05.723Z | observation_span_recorded |  |  |  |
| 44747 | 2026-09-08T21:01:06.488Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a91a279937504207840332973be83f10 |
| 44748 | 2026-09-08T21:01:06.639Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44749 | 2026-09-08T21:01:07.459Z | patch_surface_observed |  |  |  |
| 44750 | 2026-09-08T21:01:07.674Z | observation_span_recorded |  |  |  |
| 44751 | 2026-09-08T21:01:07.922Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a91a279937504207840332973be83f10 |
| 44752 | 2026-09-08T21:01:08.091Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44753 | 2026-09-08T21:01:08.813Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bcb9533c87e955fe; input_fingerprint=935a1f13f031cc984baadc3352bc084f5f16eadc5e49d395974c6475dcad621c |
| 44754 | 2026-09-08T21:01:09.158Z | managed_process_admitted |  |  | owner=default |
| 44755 | 2026-09-08T21:01:09.468Z | managed_process_started |  |  | owner=default |
| 44756 | 2026-09-08T21:01:11.957Z | managed_process_terminal |  |  | owner=default |
| 44757 | 2026-09-08T21:01:12.307Z | proof_recorded |  |  | stage_id=check:bcb9533c87e955fe; status=passed; cache_hit=False; input_fingerprint=935a1f13f031cc984baadc3352bc084f5f16eadc5e49d395974c6475dcad621c |
| 44758 | 2026-09-08T21:01:12.508Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:23efc2d04b2baee1; input_fingerprint=36c812eb037be8f18e242cfdcf98e4c5ecc3ed212ad6fffcb6b2e46e0e6c7775 |
| 44759 | 2026-09-08T21:01:12.840Z | managed_process_admitted |  |  | owner=default |
| 44760 | 2026-09-08T21:01:13.174Z | managed_process_started |  |  | owner=default |
| 44761 | 2026-09-08T21:01:13.574Z | managed_process_terminal |  |  | owner=default |
| 44762 | 2026-09-08T21:01:13.892Z | proof_recorded |  |  | stage_id=check:23efc2d04b2baee1; status=passed; cache_hit=False; input_fingerprint=36c812eb037be8f18e242cfdcf98e4c5ecc3ed212ad6fffcb6b2e46e0e6c7775 |
| 44763 | 2026-09-08T21:01:14.706Z | observation_span_recorded |  |  |  |
| 44764 | 2026-09-08T21:01:14.848Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44765 | 2026-09-08T21:03:53.269Z | quality_outcome_recorded |  |  |  |
| 44766 | 2026-09-08T21:03:53.427Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44767 | 2026-09-08T21:03:53.689Z | observation_span_recorded |  |  |  |
| 44768 | 2026-09-08T21:03:53.909Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:bcb9533c87e955fe | passed | 935a1f13f031cc984baadc3352bc084f5f16eadc5e49d395974c6475dcad621c | False | 3201 | 0 |
| check:23efc2d04b2baee1 | passed | 36c812eb037be8f18e242cfdcf98e4c5ecc3ed212ad6fffcb6b2e46e0e6c7775 | False | 1084 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a80af312e2a4450aa59d5a28539eec53 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 597b6d914aa043de8ba0da824fb448a85dc1e3a990e8adefa427f0cdb2f888b5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `96e95ba4f5158dfeaeb7c5ace76cb1c36075ac74610f71eeea4b948bd24df047`
