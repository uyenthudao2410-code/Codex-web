# Orchestration Wave 1

- Run: `0e322e678a1c47a7a7ab2a2a5bceafe2`
- Wave: `7b7a6fb999be47ae8706aa7455b99947`
- Objective: Apply the bounded Execution Fabric observability/control implementation now, using the prepared source context. Required concrete behavior: (1) in MCPHandler.control_orchestration_snapshot, derive runtime_activity only from authoritative existing state: active_tool_calls; actual running/starting ExecSession commands under sessions_lock; running process-managed jobs from execution_resource_governor snapshot if an existing public snapshot method is available, otherwise project currently running ExecSession fields only; active background operations from process memory/ledger; active delegations; current real write lease. runtime_activity must include a top-level state in {idle,active,writing,delegating}, counts, and a bounded managed_jobs list with command_id/job_id/root_pid/lifecycle_state/resource_class/run_id/wave_id when available. Do not add any process-kill authority. (2) client projection must preserve last_seen_at and add an evidence-based activity_state: active when within existing 45s window; recent when last_seen exists but outside 45s; no_recent_signal when no timestamp. The boolean online may remain for controller-lease compatibility, but UI must not label it connectivity. (3) renderer/panel.js must use runtime_activity to label Execution Hub: SẴN SÀNG/ĐANG HOẠT ĐỘNG/ĐANG GHI/ĐANG ỦY QUYỀN, with endpoint snapshot presence meaning available/idle rather than active. Frontend cards must show ACTIVE/RECENT/NO RECENT SIGNAL (Vietnamese wording is fine) based on activity_state, not ONLINE/OFFLINE. MCP Write & Proof remains active only for actual write lease. Provider lanes remain unchanged evidence-gated. (4) add a small Managed Runtime Activity section in existing advanced operations showing active tool calls, active commands/background operations and managed jobs read-only. Do not add Stop unless an already-existing panel-safe command_control IPC exists; current code only exposes task_control, so this wave should be observation-only. (5) add focused source/UI regression coverage in existing tests/control-panel.test.js and, if practical, the narrowest Python test file for orchestration snapshot semantics. Preserve all unrelated WIP. No scheduler/worktree/capacity work, no restart/live activation, no commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `6c5f6f0d890b3854b961e4113dce989d305c160d084d3f767571e72a25c21c40`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21309 | 2026-08-19T09:35:41.976Z | run_started |  | PREFLIGHT |  |
| 21310 | 2026-08-19T09:35:49.697Z | solution_shadow_recommended |  |  |  |
| 21311 | 2026-08-19T09:36:01.838Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21312 | 2026-08-19T09:36:01.994Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21313 | 2026-08-19T09:36:02.126Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 21314 | 2026-08-19T09:36:02.301Z | state_transition | READY | ROUTED | reason=route_selected |
| 21315 | 2026-08-19T09:36:02.758Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ee6e0ed9d2e04d35a9d47b405e4f86c5 |
| 21316 | 2026-08-19T09:36:02.936Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21317 | 2026-08-19T09:36:03.525Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ee6e0ed9d2e04d35a9d47b405e4f86c5 |
| 21318 | 2026-08-19T09:36:03.666Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21319 | 2026-08-19T09:36:04.019Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:99822a7899270cff; input_fingerprint=68c450a9621c38f40f3465df691d905822d283f44b70153031ebe023fd52cf18 |
| 21320 | 2026-08-19T09:36:04.552Z | managed_process_admitted |  |  | owner=default |
| 21321 | 2026-08-19T09:36:04.829Z | managed_process_started |  |  | owner=default |
| 21322 | 2026-08-19T09:36:05.221Z | managed_process_terminal |  |  | owner=default |
| 21323 | 2026-08-19T09:36:05.553Z | proof_recorded |  |  | stage_id=check:99822a7899270cff; status=passed; cache_hit=False; input_fingerprint=68c450a9621c38f40f3465df691d905822d283f44b70153031ebe023fd52cf18 |
| 21324 | 2026-08-19T09:36:05.699Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e1f0debba7bd2a054649bb10877f68fdccdc9be124a421e0b76ab5585b635161 |
| 21325 | 2026-08-19T09:36:06.129Z | managed_process_admitted |  |  | owner=default |
| 21326 | 2026-08-19T09:36:06.427Z | managed_process_started |  |  | owner=default |
| 21327 | 2026-08-19T09:36:06.844Z | managed_process_terminal |  |  | owner=default |
| 21328 | 2026-08-19T09:36:07.295Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=e1f0debba7bd2a054649bb10877f68fdccdc9be124a421e0b76ab5585b635161 |
| 21329 | 2026-08-19T09:36:07.447Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21330 | 2026-08-19T09:36:17.192Z | failure_observed | ACCEPTING | ACCEPTING | reason=Rejected: no source changes were produced (affected_files empty, git_diff null). Existing focused test pass does not satisfy the requested Execution Fabric implementation. Replan will use an explicit source patch against the inspected mcp_http_handler.py and panel files, preserving unrelated WIP.; failure_class=SOL_REJECTED |
| 21331 | 2026-08-19T09:36:17.371Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 21332 | 2026-08-19T09:36:17.539Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:99822a7899270cff | passed | 68c450a9621c38f40f3465df691d905822d283f44b70153031ebe023fd52cf18 | False | 1144 | 0 |
| verify:tests | passed | e1f0debba7bd2a054649bb10877f68fdccdc9be124a421e0b76ab5585b635161 | False | 1139 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `9d36f58d14e294bc014656f72c21b1870f2b7fdee08cc4b8b6d7c0ff14a5b024`
