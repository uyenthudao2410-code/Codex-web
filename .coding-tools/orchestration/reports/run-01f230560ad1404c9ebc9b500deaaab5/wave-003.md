# Orchestration Wave 3

- Run: `01f230560ad1404c9ebc9b500deaaab5`
- Wave: `75232bd7fb3f4a5398630f40a6c46459`
- Objective: C01/M02 machine-A pre-reboot artifact step for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Rebuild the current Windows NSIS installer from the exact accepted Recovery Supervisor source, prove the newly produced win-unpacked payload with the packaged Recovery smoke without rebuilding it again, and record exact installer/executable/resource hashes. Do not install or uninstall applications, alter the production Recovery Supervisor/Scheduled Task/runtime state, reboot/logoff, edit repository source, commit, push, publish, release, or deploy. Preserve concurrent dirty work.
- Objective revision: `3`
- Objective SHA-256: `999f94ab9ae8d32043cd744653af9400b99fcade5c7ff50fd3cd3c764f668f84`
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
| 58574 | 2026-09-15T08:39:36.073Z | wave_replanned |  | PREFLIGHT | reason=The prior wave was explicitly rejected because its build_command was not executed under the run's workflow token; only the preflight proof existed. Changed strategy: execute npm run dist itself as a durable check command, then run packaged-recovery-smoke.js against that exact newly built win-unpacked tree, then hash the installer and packaged resources in a final check. This materially changes the proof path while preserving the same scope and no reboot/install authority. |
| 58575 | 2026-09-15T08:39:36.688Z | observation_span_recorded |  |  |  |
| 58576 | 2026-09-15T08:39:37.740Z | observation_span_recorded |  |  |  |
| 58577 | 2026-09-15T08:39:38.258Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58578 | 2026-09-15T08:39:38.567Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 58579 | 2026-09-15T08:39:38.949Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58580 | 2026-09-15T08:39:39.165Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58581 | 2026-09-15T08:39:39.959Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58582 | 2026-09-15T08:39:40.393Z | state_transition | READY | ROUTED | reason=route_selected |
| 58583 | 2026-09-15T08:39:40.913Z | observation_span_recorded |  |  |  |
| 58584 | 2026-09-15T08:39:41.826Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5e2d0a8552064f7886115d573f101f2f |
| 58585 | 2026-09-15T08:39:42.029Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58586 | 2026-09-15T08:39:42.904Z | observation_span_recorded |  |  |  |
| 58587 | 2026-09-15T08:39:43.467Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5e2d0a8552064f7886115d573f101f2f |
| 58588 | 2026-09-15T08:39:43.863Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58589 | 2026-09-15T08:39:44.534Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a4e5881b60adabbb; input_fingerprint=20ab327e2ba888de829aaa93034b7caf2c96d3f5708374a27cedbf40b9eb324f |
| 58590 | 2026-09-15T08:39:45.083Z | managed_process_admitted |  |  | owner=default |
| 58591 | 2026-09-15T08:39:45.736Z | managed_process_started |  |  | owner=default |
| 58592 | 2026-09-15T08:39:46.702Z | managed_process_terminal |  |  | owner=default |
| 58593 | 2026-09-15T08:39:47.661Z | proof_recorded |  |  | stage_id=check:a4e5881b60adabbb; status=passed; cache_hit=False; input_fingerprint=20ab327e2ba888de829aaa93034b7caf2c96d3f5708374a27cedbf40b9eb324f |
| 58594 | 2026-09-15T08:39:48.026Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e449d13f93c687d1; input_fingerprint=29795db01241e93243124edf4158693b14080ca5afd2772a5f37b1bbff8b6c72 |
| 58595 | 2026-09-15T08:39:48.789Z | managed_process_admitted |  |  | owner=default |
| 58596 | 2026-09-15T08:39:49.624Z | managed_process_started |  |  | owner=default |
| 58597 | 2026-09-15T08:49:30.130Z | managed_process_terminal |  |  | owner=default |
| 58598 | 2026-09-15T08:49:31.359Z | proof_recorded |  |  | stage_id=check:e449d13f93c687d1; status=passed; cache_hit=False; input_fingerprint=29795db01241e93243124edf4158693b14080ca5afd2772a5f37b1bbff8b6c72 |
| 58599 | 2026-09-15T08:49:31.942Z | observation_span_recorded |  |  |  |
| 58600 | 2026-09-15T08:49:32.667Z | failure_observed | PROVING | PROVING | failure_class=PROOF_TIMEOUT |
| 58601 | 2026-09-15T08:49:33.329Z | state_transition | PROVING | REPLAN | reason=PROOF_TIMEOUT; failure_class=PROOF_TIMEOUT |
| 58602 | 2026-09-15T08:49:33.781Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58603 | 2026-09-15T08:50:03.361Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a4e5881b60adabbb | passed | 20ab327e2ba888de829aaa93034b7caf2c96d3f5708374a27cedbf40b9eb324f | False | 2215 | 0 |
| check:e449d13f93c687d1 | passed | 29795db01241e93243124edf4158693b14080ca5afd2772a5f37b1bbff8b6c72 | False | 581834 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `144`
- Chain head: `42c884cae51c8a7286a902f5cde990737dd7736deba3ca0d5eceee1bc409ed53`
