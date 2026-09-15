# Orchestration Wave 4

- Run: `01f230560ad1404c9ebc9b500deaaab5`
- Wave: `c5754eb770c84b82a43c8a90726cc779`
- Objective: C01/M02 machine-A pre-reboot artifact step for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Produce a fresh exact-current NSIS installer without re-running the already-proven broad suites that exceeded the 600s wrapper. Reuse the accepted Recovery source/package proofs on the unchanged worktree, run only the canonical packaging sub-steps that follow test:all, then run the packaged Recovery smoke against the newly produced win-unpacked tree and record exact installer/executable/resource hashes. Do not install/uninstall applications, alter the production Recovery Supervisor/Scheduled Task/runtime state, reboot/logoff, edit repository source, commit, push, publish, release, or deploy. Preserve concurrent dirty work.
- Objective revision: `4`
- Objective SHA-256: `bea136d2a27a82f8c7425aeb2acff4af370819c75f9c20ed7bdaa51f3bc27111`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58604 | 2026-09-15T08:50:28.796Z | wave_replanned |  | PREFLIGHT | reason=The previous wave was not accepted because the full canonical npm run dist exceeded the 600s proof budget while still inside test:all; Node 825/825 and repository secret/source-root guards had passed, and no packaging sub-step had begun. This is not an unchanged retry. Per repository policy, reuse successful exact-fingerprint Recovery proofs and change strategy to execute only the canonical packaging sub-steps that occur after test:all (icon:build, clean-dist, electron-builder --win nsis), followed by a fresh packaged-recovery smoke and exact artifact hashing. This avoids re-running broad suites already covered by accepted checkpoints and stays within the C01 artifact boundary. |
| 58605 | 2026-09-15T08:50:29.616Z | observation_span_recorded |  |  |  |
| 58606 | 2026-09-15T08:50:30.563Z | observation_span_recorded |  |  |  |
| 58607 | 2026-09-15T08:50:31.146Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58608 | 2026-09-15T08:50:31.640Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 58609 | 2026-09-15T08:50:32.085Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58610 | 2026-09-15T08:50:32.431Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58611 | 2026-09-15T08:50:32.858Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58612 | 2026-09-15T08:50:33.322Z | state_transition | READY | ROUTED | reason=route_selected |
| 58613 | 2026-09-15T08:50:33.832Z | observation_span_recorded |  |  |  |
| 58614 | 2026-09-15T08:50:35.078Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=131eaab84838441686b550c1a80e5c73 |
| 58615 | 2026-09-15T08:50:35.643Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58616 | 2026-09-15T08:50:36.454Z | observation_span_recorded |  |  |  |
| 58617 | 2026-09-15T08:50:37.280Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=131eaab84838441686b550c1a80e5c73 |
| 58618 | 2026-09-15T08:50:37.638Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58619 | 2026-09-15T08:50:38.518Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5f6f4ef4ef9b5c63; input_fingerprint=9d4bfbf2a5183e8068f66e0b485480dd01bb96fe96753b7e62326d1325f79511 |
| 58620 | 2026-09-15T08:50:39.443Z | managed_process_admitted |  |  | owner=default |
| 58621 | 2026-09-15T08:50:40.267Z | managed_process_started |  |  | owner=default |
| 58622 | 2026-09-15T08:50:41.243Z | managed_process_terminal |  |  | owner=default |
| 58623 | 2026-09-15T08:50:42.444Z | proof_recorded |  |  | stage_id=check:5f6f4ef4ef9b5c63; status=passed; cache_hit=False; input_fingerprint=9d4bfbf2a5183e8068f66e0b485480dd01bb96fe96753b7e62326d1325f79511 |
| 58624 | 2026-09-15T08:50:42.992Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3f6cd4f99a57ca57; input_fingerprint=6b35ec405bddeaa091e1901f94aa61980b6ab5670fa288992802c772c95d2462 |
| 58625 | 2026-09-15T08:50:44.242Z | managed_process_admitted |  |  | owner=default |
| 58626 | 2026-09-15T08:50:45.377Z | managed_process_started |  |  | owner=default |
| 58627 | 2026-09-15T08:51:58.035Z | managed_process_terminal |  |  | owner=default |
| 58628 | 2026-09-15T08:51:58.943Z | proof_recorded |  |  | stage_id=check:3f6cd4f99a57ca57; status=passed; cache_hit=False; input_fingerprint=6b35ec405bddeaa091e1901f94aa61980b6ab5670fa288992802c772c95d2462 |
| 58629 | 2026-09-15T08:51:59.439Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:470e7e0d382448b5; input_fingerprint=2d8d2d537134df5bb5f39bdc2e16757838b7cc6236cd354b5a16c9cdc392d759 |
| 58630 | 2026-09-15T08:52:00.789Z | managed_process_admitted |  |  | owner=default |
| 58631 | 2026-09-15T08:52:02.346Z | managed_process_started |  |  | owner=default |
| 58632 | 2026-09-15T08:52:12.153Z | managed_process_terminal |  |  | owner=default |
| 58633 | 2026-09-15T08:52:13.259Z | proof_recorded |  |  | stage_id=check:470e7e0d382448b5; status=passed; cache_hit=False; input_fingerprint=2d8d2d537134df5bb5f39bdc2e16757838b7cc6236cd354b5a16c9cdc392d759 |
| 58634 | 2026-09-15T08:52:13.907Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0457f5555654ef62; input_fingerprint=d2f79ebd778a3007b14463449325a568366b2ff55650b8c354bee840909165f6 |
| 58635 | 2026-09-15T08:52:14.950Z | managed_process_admitted |  |  | owner=default |
| 58636 | 2026-09-15T08:52:15.548Z | managed_process_started |  |  | owner=default |
| 58637 | 2026-09-15T08:52:17.354Z | managed_process_terminal |  |  | owner=default |
| 58638 | 2026-09-15T08:52:18.426Z | proof_recorded |  |  | stage_id=check:0457f5555654ef62; status=passed; cache_hit=False; input_fingerprint=d2f79ebd778a3007b14463449325a568366b2ff55650b8c354bee840909165f6 |
| 58639 | 2026-09-15T08:52:19.238Z | observation_span_recorded |  |  |  |
| 58640 | 2026-09-15T08:52:20.069Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 58641 | 2026-09-15T08:52:20.407Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 58642 | 2026-09-15T08:55:10.355Z | continuity_telemetry_recorded |  |  |  |
| 58643 | 2026-09-15T08:55:24.681Z | quality_outcome_recorded |  |  |  |
| 58644 | 2026-09-15T08:55:25.149Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 58645 | 2026-09-15T08:55:26.417Z | observation_span_recorded |  |  |  |
| 58646 | 2026-09-15T08:55:26.993Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 58647 | 2026-09-15T08:55:27.404Z | observation_span_recorded |  |  |  |
| 58648 | 2026-09-15T08:55:27.963Z | observation_span_recorded |  |  |  |
| 58649 | 2026-09-15T08:55:28.303Z | continuity_telemetry_recorded |  |  |  |
| 58650 | 2026-09-15T08:55:55.875Z | continuity_telemetry_recorded |  |  |  |
| 58651 | 2026-09-15T08:55:56.449Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5f6f4ef4ef9b5c63 | passed | 9d4bfbf2a5183e8068f66e0b485480dd01bb96fe96753b7e62326d1325f79511 | False | 2814 | 0 |
| check:3f6cd4f99a57ca57 | passed | 6b35ec405bddeaa091e1901f94aa61980b6ab5670fa288992802c772c95d2462 | False | 74420 | 0 |
| check:470e7e0d382448b5 | passed | 2d8d2d537134df5bb5f39bdc2e16757838b7cc6236cd354b5a16c9cdc392d759 | False | 12820 | 0 |
| check:0457f5555654ef62 | passed | d2f79ebd778a3007b14463449325a568366b2ff55650b8c354bee840909165f6 | False | 3691 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| daaa58b32e4b4efd9a1dd0a94c7240fd | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | d674752cc7e6c397d259c8dc8951f90c641fa8431657a7c3e3905a130708b414 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `144`
- Chain head: `42c884cae51c8a7286a902f5cde990737dd7736deba3ca0d5eceee1bc409ed53`
