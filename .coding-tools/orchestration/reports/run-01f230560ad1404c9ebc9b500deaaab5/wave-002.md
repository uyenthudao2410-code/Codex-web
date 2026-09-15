# Orchestration Wave 2

- Run: `01f230560ad1404c9ebc9b500deaaab5`
- Wave: `76dda3bac45f4a8bad55f80539a11882`
- Objective: C01/M02 machine-A pre-reboot artifact step for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Rebuild only the exact current Windows NSIS installer from the current worktree whose current Recovery Supervisor SHA256 is 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab and whose already-accepted win-unpacked executable SHA256 is cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c. The prior persistent acceptance app is stale and must not be used as current reboot evidence. Use the canonical npm run dist command only after exact-byte preflight. Do not install/uninstall applications, alter Recovery Supervisor/Scheduled Task/runtime state, reboot/logoff, edit repository source, commit, push, publish, release, or deploy. Preserve concurrent dirty work.
- Objective revision: `2`
- Objective SHA-256: `491ad94b26307548e0ea7d7d8db8145a77cf6e04641d5f72ab1879fa0371cc02`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58546 | 2026-09-15T08:35:31.110Z | wave_replanned |  | PREFLIGHT | reason=The prior execute request entered REPLAN before any command/build because the execute contract rejected a build-only plan and then its prepared binding was no longer executable. No side effect occurred. Strategy is narrowed to a fresh build_release prepare wave whose only intended mutation is dist artifact regeneration after an exact-byte preflight; installed state and reboot remain out of scope. |
| 58547 | 2026-09-15T08:35:31.656Z | observation_span_recorded |  |  |  |
| 58548 | 2026-09-15T08:35:49.112Z | observation_span_recorded |  |  |  |
| 58549 | 2026-09-15T08:35:49.415Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58550 | 2026-09-15T08:37:08.846Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58551 | 2026-09-15T08:37:09.096Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58552 | 2026-09-15T08:37:09.540Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58553 | 2026-09-15T08:37:09.946Z | state_transition | READY | ROUTED | reason=route_selected |
| 58554 | 2026-09-15T08:37:10.314Z | observation_span_recorded |  |  |  |
| 58555 | 2026-09-15T08:37:11.260Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e8b9cd80b7364c60bbd7767cdf468574 |
| 58556 | 2026-09-15T08:37:11.524Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58557 | 2026-09-15T08:37:12.312Z | observation_span_recorded |  |  |  |
| 58558 | 2026-09-15T08:37:12.866Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e8b9cd80b7364c60bbd7767cdf468574 |
| 58559 | 2026-09-15T08:37:13.166Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58560 | 2026-09-15T08:37:13.746Z | proof_cache_miss |  |  | reason=cold; stage_id=check:93db338b0bcb346a; input_fingerprint=1dd282aab12959ba4cd534c16aa15ac4f58db4355abe571c06facbc758e3d892 |
| 58561 | 2026-09-15T08:37:14.474Z | managed_process_admitted |  |  | owner=default |
| 58562 | 2026-09-15T08:37:15.089Z | managed_process_started |  |  | owner=default |
| 58563 | 2026-09-15T08:37:16.068Z | managed_process_terminal |  |  | owner=default |
| 58564 | 2026-09-15T08:37:16.699Z | proof_recorded |  |  | stage_id=check:93db338b0bcb346a; status=passed; cache_hit=False; input_fingerprint=1dd282aab12959ba4cd534c16aa15ac4f58db4355abe571c06facbc758e3d892 |
| 58565 | 2026-09-15T08:37:17.030Z | observation_span_recorded |  |  |  |
| 58566 | 2026-09-15T08:37:17.327Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 58567 | 2026-09-15T08:37:17.827Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 58568 | 2026-09-15T08:37:40.336Z | continuity_telemetry_recorded |  |  |  |
| 58569 | 2026-09-15T08:37:53.421Z | observation_span_recorded |  |  |  |
| 58570 | 2026-09-15T08:37:53.739Z | failure_observed | ACCEPTING | ACCEPTING | reason=Rejecting this wave because only the exact-byte preflight executed. The canonical npm run dist build did not execute and build_report is null, so the stated artifact-rebuild objective is not proven. No installed-state or reboot side effect occurred. Replan with npm run dist as an explicit check command so its exit status becomes durable proof before any installer replacement or reboot preparation.; failure_class=SOL_REJECTED |
| 58571 | 2026-09-15T08:37:54.234Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 58572 | 2026-09-15T08:37:54.706Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58573 | 2026-09-15T08:39:07.211Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:93db338b0bcb346a | passed | 1dd282aab12959ba4cd534c16aa15ac4f58db4355abe571c06facbc758e3d892 | False | 2209 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `144`
- Chain head: `42c884cae51c8a7286a902f5cde990737dd7736deba3ca0d5eceee1bc409ed53`
