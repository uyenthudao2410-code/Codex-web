# Orchestration Wave 2

- Run: `fe863a45563b4725af4804ecf05f8a03`
- Wave: `9895cded293c4d8685753dcd1839baaa`
- Objective: Natural #8: fix the embedded token-dashboard double-poll defect. The main manager parent and the embedded token-dashboard child both load renderer/control-center.js, whose unconditional initial refresh plus pollControlCenter loop independently call lightweightSnapshot/liveOrchestration. Make embedded=1 same-origin child mode passive: consume the parent's coding-tools:overview-pulse and relay coding-tools:overview-refresh-request back to the parent without starting its own Control Center poll loop. Standalone behavior and fail-safe fallback must remain unchanged. Preserve all existing dirty WIP and do not touch renderer/dashboard.js, renderer/index.html, or renderer/token-dashboard.html.
- Objective revision: `1`
- Objective SHA-256: `2e9a10748b0adb34253075312694eed1acbb3c395a46dd4bd40d8b7fd0b98e8d`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `b635c38a4a678b02ee546c998e242ba8d725df04b2ceea944323236025ddfe88`
- Contract fingerprint: `f904045ca23b05610bf8ef5e9d46afc6cedd44217e64f4a69368022191ad859f`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45740 | 2026-09-09T12:15:02.910Z | wave_replanned |  | PREFLIGHT | reason=Canonical EOCL audit plus exact current-byte inspection prove Wave 1 already wrote exactly the intended two files and recorded two green proofs; the prior rejection was caused by contradictory/stale projection data. Changed REPLAN strategy: do not replay or rewrite the patch. Create the next wave on the same RUN, exact-byte adopt the current intended files, then rerun focused proof against those bytes before final acceptance. |
| 45741 | 2026-09-09T12:15:03.180Z | observation_span_recorded |  |  |  |
| 45742 | 2026-09-09T12:15:03.987Z | observation_span_recorded |  |  |  |
| 45743 | 2026-09-09T12:15:04.146Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45744 | 2026-09-09T12:15:21.319Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 45745 | 2026-09-09T12:15:21.551Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 45746 | 2026-09-09T12:15:21.724Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 45747 | 2026-09-09T12:15:21.941Z | state_transition | READY | ROUTED | reason=route_selected |
| 45748 | 2026-09-09T12:15:22.148Z | observation_span_recorded |  |  |  |
| 45749 | 2026-09-09T12:15:23.211Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=820fdfd4efe6436dad21ab086b9481d0 |
| 45750 | 2026-09-09T12:15:23.365Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 45751 | 2026-09-09T12:15:24.125Z | existing_file_adoption_observed |  |  |  |
| 45752 | 2026-09-09T12:15:24.411Z | observation_span_recorded |  |  |  |
| 45753 | 2026-09-09T12:15:24.679Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=820fdfd4efe6436dad21ab086b9481d0 |
| 45754 | 2026-09-09T12:15:24.795Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 45755 | 2026-09-09T12:15:25.527Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4c7dd88e5c7b8980; input_fingerprint=a8decc7ce1524d5d22890d5e7e1146ff1e5aaf29f8c83d38d0016056052c8d2e |
| 45756 | 2026-09-09T12:15:25.937Z | managed_process_admitted |  |  | owner=default |
| 45757 | 2026-09-09T12:15:26.254Z | managed_process_started |  |  | owner=default |
| 45758 | 2026-09-09T12:15:26.820Z | managed_process_terminal |  |  | owner=default |
| 45759 | 2026-09-09T12:15:27.168Z | proof_recorded |  |  | stage_id=check:4c7dd88e5c7b8980; status=passed; cache_hit=False; input_fingerprint=a8decc7ce1524d5d22890d5e7e1146ff1e5aaf29f8c83d38d0016056052c8d2e |
| 45760 | 2026-09-09T12:15:27.332Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0fc241a836a931dfbcdb13614af5cf5464d2d2e9a0434943c39bcef06f37bddf |
| 45761 | 2026-09-09T12:15:27.745Z | managed_process_admitted |  |  | owner=default |
| 45762 | 2026-09-09T12:15:28.061Z | managed_process_started |  |  | owner=default |
| 45763 | 2026-09-09T12:15:28.544Z | managed_process_terminal |  |  | owner=default |
| 45764 | 2026-09-09T12:15:29.734Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0fc241a836a931dfbcdb13614af5cf5464d2d2e9a0434943c39bcef06f37bddf |
| 45765 | 2026-09-09T12:15:29.953Z | observation_span_recorded |  |  |  |
| 45766 | 2026-09-09T12:15:30.128Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 45767 | 2026-09-09T12:17:25.346Z | managed_process_admitted |  |  | owner=default |
| 45768 | 2026-09-09T12:17:25.670Z | managed_process_started |  |  | owner=default |
| 45769 | 2026-09-09T12:18:43.428Z | managed_process_terminal |  |  | owner=default |
| 45770 | 2026-09-09T12:23:28.308Z | quality_outcome_recorded |  |  |  |
| 45771 | 2026-09-09T12:23:28.615Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 45772 | 2026-09-09T12:23:29.065Z | observation_span_recorded |  |  |  |
| 45773 | 2026-09-09T12:23:29.489Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4c7dd88e5c7b8980 | passed | a8decc7ce1524d5d22890d5e7e1146ff1e5aaf29f8c83d38d0016056052c8d2e | False | 1245 | 0 |
| verify:tests | passed | 0fc241a836a931dfbcdb13614af5cf5464d2d2e9a0434943c39bcef06f37bddf | False | 2000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 78a25177a2ff4c12b23d4f14324cebfc | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 08a6a81a1dbf450302cd85a39b536fd30dbff4cfb8a5b56a99bb841e9204165e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `a8c726e07892fb2fd0bd94e4731986b0e599334e455be54e447c87c500aab371`
