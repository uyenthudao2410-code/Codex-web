# Orchestration Wave 2

- Run: `faf5c824a6ba4fe1808e3feb9fff1348`
- Wave: `7e99b27fa76945feaa33ea7f0611c969`
- Objective: Replan only the artifact hash-binding check after the previous command failed because helper name H resolved to PowerShell alias h/Get-History. Reuse the already-passed focused Recovery Supervisor tests and diff-check from the prior wave; do not rerun them. Use an unambiguous helper name GetFileSha to compare exact current supervisor source SHA with dist/win-unpacked packaged copy and LocalAppData acceptance packaged copy, and report current installer SHA/size. If any existing packaged supervisor copy differs from source, fail closed so the installer is not used for reboot acceptance. No source edit, install, restart, reboot, commit, push, release, publish, or deploy.
- Objective revision: `2`
- Objective SHA-256: `5acb1e3390468608cf80561d7553383b43d00a633b914639187954aafa156ce1`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `bc1ac2551c293b3991d24330265bcc28d782be3a28a5881e1b94a7ecf19b4945`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59481 | 2026-09-15T10:31:23.177Z | wave_replanned |  | PREFLIGHT | reason=The only failed stage was a diagnostic harness namespace collision: PowerShell alias h/Get-History shadowed helper H. Source tests and diff-check already passed. Change only the helper name to GetFileSha and rerun the hash-binding stage. |
| 59482 | 2026-09-15T10:31:23.929Z | observation_span_recorded |  |  |  |
| 59483 | 2026-09-15T10:31:24.788Z | observation_span_recorded |  |  |  |
| 59484 | 2026-09-15T10:31:25.274Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59485 | 2026-09-15T10:31:25.859Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59486 | 2026-09-15T10:31:26.335Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59487 | 2026-09-15T10:31:26.685Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59488 | 2026-09-15T10:31:27.060Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59489 | 2026-09-15T10:31:27.581Z | state_transition | READY | ROUTED | reason=route_selected |
| 59490 | 2026-09-15T10:31:28.247Z | observation_span_recorded |  |  |  |
| 59491 | 2026-09-15T10:31:29.523Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9895b43f1e294524949b1429c9bcad88 |
| 59492 | 2026-09-15T10:31:30.007Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59493 | 2026-09-15T10:31:30.814Z | observation_span_recorded |  |  |  |
| 59494 | 2026-09-15T10:31:31.616Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9895b43f1e294524949b1429c9bcad88 |
| 59495 | 2026-09-15T10:31:32.029Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59496 | 2026-09-15T10:31:32.711Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f9429f25739da71c; input_fingerprint=fdb4657eaa2d6c6af2716e270809bde86948a45a66a5c13bc1b28493fdb21165 |
| 59497 | 2026-09-15T10:31:33.573Z | managed_process_admitted |  |  | owner=default |
| 59498 | 2026-09-15T10:31:34.239Z | managed_process_started |  |  | owner=default |
| 59499 | 2026-09-15T10:31:35.408Z | managed_process_terminal |  |  | owner=default |
| 59500 | 2026-09-15T10:31:36.322Z | proof_recorded |  |  | stage_id=check:f9429f25739da71c; status=passed; cache_hit=False; input_fingerprint=fdb4657eaa2d6c6af2716e270809bde86948a45a66a5c13bc1b28493fdb21165 |
| 59501 | 2026-09-15T10:31:37.246Z | observation_span_recorded |  |  |  |
| 59502 | 2026-09-15T10:31:37.779Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 59503 | 2026-09-15T10:31:38.147Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 59504 | 2026-09-15T10:32:45.154Z | quality_outcome_recorded |  |  |  |
| 59505 | 2026-09-15T10:32:45.654Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 59506 | 2026-09-15T10:32:46.556Z | observation_span_recorded |  |  |  |
| 59507 | 2026-09-15T10:32:47.642Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 59508 | 2026-09-15T10:32:48.770Z | observation_span_recorded |  |  |  |
| 59509 | 2026-09-15T10:32:49.227Z | observation_span_recorded |  |  |  |
| 59510 | 2026-09-15T10:32:49.458Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f9429f25739da71c | passed | fdb4657eaa2d6c6af2716e270809bde86948a45a66a5c13bc1b28493fdb21165 | False | 2717 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d8824f344e9b406abe7df8ec3a8352a7 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | e4a4bd8e2d6935747f36dd4f6175e0aed3a1fa8aaa30114d9b33cff6e5da87a2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `64`
- Chain head: `29b1f1576bfabee0a3a3b31787a9440a37b02f45e0a53f3c975243a5bebd3276`
