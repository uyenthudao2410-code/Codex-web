# Orchestration Wave 1

- Run: `65a23c33019c49cf92fd133cf09db2bc`
- Wave: `cb6b00f7cd34400190ee1b02839b0dd4`
- Objective: Implement the smallest useful Execution Fabric observability/control fix only. Do NOT add multi-session scheduling, worktree pools, worker scaling, routing changes, or any new orchestration architecture. Preserve all existing WIP, especially the current MCP2026 task-context/session-isolation and usage-accounting changes. Scope: (1) make /__control/orchestration expose an authoritative runtime_activity projection from existing runtime/resource data, including active tool calls, active commands/managed jobs, background operations where already tracked, last tool-call/client timestamps/identity when available, and mutation/write activity; never fabricate connection state; (2) make Execution Fabric renderer distinguish endpoint/runtime availability from actual activity, e.g. ready/idle vs active vs writing/delegating, instead of treating snapshot presence as 'running'; (3) replace misleading ChatWeb binary online/offline semantics with evidence-based active/recent/no-recent-signal states using existing last_seen/request activity, clearly named so idle does not imply disconnected; keep the existing 45s active window only as an activity threshold rather than a connectivity claim; (4) surface managed command/job activity in the panel with command/job id, PID/state/resource class and observe/stop controls only if an existing safe command-control authority/endpoint can be reused. Do not add a second process-kill authority; if no safe existing panel control route exists, implement observation-only and make that explicit in UI; (5) keep MCP Write & Proof semantics unchanged: it is active only for real write lease/fence; provider lanes remain evidence-gated and only light up from real delegations; (6) add focused regression tests for orchestration snapshot activity semantics and panel state mapping, including idle snapshot, active tool/command, writing, recent ChatWeb, and no-recent-signal cases. Do not modify roadmap/phases except minimal current-behavior docs if a public UI semantic changed. No restart/live activation, no commit/push.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `49d8cba97146758047f99ad16ab181281624cdc6635a2183f433e1a4a5743566`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21205 | 2026-08-19T09:15:30.816Z | run_started |  | PREFLIGHT |  |
| 21206 | 2026-08-19T09:15:41.079Z | solution_shadow_recommended |  |  |  |
| 21207 | 2026-08-19T09:15:49.878Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21208 | 2026-08-19T09:15:50.049Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21209 | 2026-08-19T09:15:50.166Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 21210 | 2026-08-19T09:15:50.300Z | state_transition | READY | ROUTED | reason=route_selected |
| 21211 | 2026-08-19T09:15:50.738Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=86160ec8a843435c9765e228ede36c3c |
| 21212 | 2026-08-19T09:15:50.871Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21213 | 2026-08-19T09:15:51.288Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=86160ec8a843435c9765e228ede36c3c |
| 21214 | 2026-08-19T09:15:51.509Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21215 | 2026-08-19T09:15:51.850Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=04ccfeabd8b1ad153b8080d8da9fccfe696f6e71997d949b446fdbb6416c7507 |
| 21216 | 2026-08-19T09:15:52.167Z | managed_process_admitted |  |  | owner=default |
| 21217 | 2026-08-19T09:15:52.488Z | managed_process_started |  |  | owner=default |
| 21218 | 2026-08-19T09:16:16.638Z | managed_process_terminal |  |  | owner=default |
| 21219 | 2026-08-19T09:16:16.930Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=04ccfeabd8b1ad153b8080d8da9fccfe696f6e71997d949b446fdbb6416c7507 |
| 21220 | 2026-08-19T09:16:17.146Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21221 | 2026-08-19T09:16:29.429Z | failure_observed | ACCEPTING | ACCEPTING | reason=Acceptance rejected: the wave produced no source changes (affected_files empty, git_diff null), so it did not implement the requested Execution Fabric observability/control behavior even though the existing npm test suite passed. Replan must inspect the exact implementation and apply a bounded patch.; failure_class=SOL_REJECTED |
| 21222 | 2026-08-19T09:16:29.594Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 21223 | 2026-08-19T09:16:29.729Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 04ccfeabd8b1ad153b8080d8da9fccfe696f6e71997d949b446fdbb6416c7507 | False | 24781 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `2a1aa655461d6e2db6325138a7461411bb35500291a538a321b8bbfc088054c7`
