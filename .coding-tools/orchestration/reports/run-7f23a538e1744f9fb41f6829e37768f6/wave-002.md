# Orchestration Wave 2

- Run: `7f23a538e1744f9fb41f6829e37768f6`
- Wave: `981c24543d054eaea6ff31c98b61f252`
- Objective: Continue the same Problem revision-2 bugfix after the pre-write validation failures. No source bytes were changed. Use the currently inspected dirty bytes as the baseline, target only stale_run_reconciliation.py plus test_exact_stale_run_reconciliation.py, and verify from resources/coding-tools-mcp with `python -m unittest discover -s tests -p test_exact_stale_run_reconciliation.py`. Implement managed_job_residue as true only for STALE_MANAGED_JOB_RESIDUE or ORPHANED_OR_FOREIGN_MANAGED_JOB, while LIVE_OWNED does not globally block an unrelated stale target. Preserve every other fail-closed guard. Do not reconcile production stale RUNs, restart, commit, push, clean, reset, or backfill history.
- Objective revision: `2`
- Objective SHA-256: `2de9050a93454a328ea3227a0889cc5d3b7fadf3e0cf7b9f8566940fb04524a5`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `49249c1e4835542db2aafc1b22d6661a366fb5eb62ca622149d3c7775983dde1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50622 | 2026-09-12T07:28:16.711Z | wave_replanned |  | PREFLIGHT | reason=Wave 8b7656c9e1e24ff6998d166de918c91f reached REPLAN without a write lease or source mutation. New evidence fixes the execution contract: the real regression module is test_exact_stale_run_reconciliation.py; its baseline is 7/7 green from the package cwd; current helper/test bytes were inspected and hashed; and adopt_existing_files is a no-write mechanism, so this implementation must patch the current prepared worktree directly rather than combine adoption and patching. |
| 50623 | 2026-09-12T07:28:16.938Z | observation_span_recorded |  |  |  |
| 50624 | 2026-09-12T07:28:28.275Z | observation_span_recorded |  |  |  |
| 50625 | 2026-09-12T07:28:28.488Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50626 | 2026-09-12T07:29:28.964Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50627 | 2026-09-12T07:29:29.183Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50628 | 2026-09-12T07:29:29.358Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 50629 | 2026-09-12T07:29:29.558Z | state_transition | READY | ROUTED | reason=route_selected |
| 50630 | 2026-09-12T07:29:29.819Z | observation_span_recorded |  |  |  |
| 50631 | 2026-09-12T07:29:30.825Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=07354759ded44a259f13605b06b73318 |
| 50632 | 2026-09-12T07:29:31.092Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50633 | 2026-09-12T07:29:32.024Z | patch_surface_observed |  |  |  |
| 50634 | 2026-09-12T07:29:32.253Z | observation_span_recorded |  |  |  |
| 50635 | 2026-09-12T07:29:32.550Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=07354759ded44a259f13605b06b73318 |
| 50636 | 2026-09-12T07:29:32.773Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50637 | 2026-09-12T07:29:33.673Z | proof_cache_miss |  |  | reason=cold; stage_id=check:51a2f478af787e1b; input_fingerprint=6a2ae8dee76beb086d0629f31585f87d7e31cc835943749b159f2eb34a58abad |
| 50638 | 2026-09-12T07:29:34.097Z | managed_process_admitted |  |  | owner=default |
| 50639 | 2026-09-12T07:29:34.497Z | managed_process_started |  |  | owner=default |
| 50640 | 2026-09-12T07:29:46.729Z | managed_process_terminal |  |  | owner=default |
| 50641 | 2026-09-12T07:29:47.123Z | proof_recorded |  |  | stage_id=check:51a2f478af787e1b; status=passed; cache_hit=False; input_fingerprint=6a2ae8dee76beb086d0629f31585f87d7e31cc835943749b159f2eb34a58abad |
| 50642 | 2026-09-12T07:29:47.350Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c32e0681039328574146a955d2ee9bc6ef8c72e306ef7c208ff1c232e82f7265 |
| 50643 | 2026-09-12T07:29:47.729Z | managed_process_admitted |  |  | owner=default |
| 50644 | 2026-09-12T07:29:48.096Z | managed_process_started |  |  | owner=default |
| 50645 | 2026-09-12T07:29:59.283Z | managed_process_terminal |  |  | owner=default |
| 50646 | 2026-09-12T07:30:00.791Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c32e0681039328574146a955d2ee9bc6ef8c72e306ef7c208ff1c232e82f7265 |
| 50647 | 2026-09-12T07:30:01.779Z | observation_span_recorded |  |  |  |
| 50648 | 2026-09-12T07:30:02.024Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50649 | 2026-09-12T07:30:02.284Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 50650 | 2026-09-12T07:34:43.350Z | continuity_telemetry_recorded |  |  |  |
| 50651 | 2026-09-12T07:35:34.752Z | managed_process_admitted |  |  | owner=default |
| 50652 | 2026-09-12T07:35:35.136Z | managed_process_started |  |  | owner=default |
| 50653 | 2026-09-12T07:35:35.855Z | managed_process_terminal |  |  | owner=default |
| 50654 | 2026-09-12T07:35:43.625Z | quality_outcome_recorded |  |  |  |
| 50655 | 2026-09-12T07:35:43.890Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50656 | 2026-09-12T07:35:44.258Z | observation_span_recorded |  |  |  |
| 50657 | 2026-09-12T07:35:44.516Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 50658 | 2026-09-12T07:35:44.851Z | observation_span_recorded |  |  |  |
| 50659 | 2026-09-12T07:35:45.083Z | observation_span_recorded |  |  |  |
| 50660 | 2026-09-12T07:35:45.339Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:51a2f478af787e1b | passed | 6a2ae8dee76beb086d0629f31585f87d7e31cc835943749b159f2eb34a58abad | False | 13080 | 0 |
| verify:tests | passed | c32e0681039328574146a955d2ee9bc6ef8c72e306ef7c208ff1c232e82f7265 | False | 13063 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3f1d395d19094c469b3c65c847cf40ac | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 99b3cbb617fcfb17ece7ec244a564bf3b1a2b4cae1ccb1080b219c72e535d94e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `c77b005a4cbacdda8dbafeb1b9c3c03f449e8fcec74d22153f8ac27cbc6d0468`
