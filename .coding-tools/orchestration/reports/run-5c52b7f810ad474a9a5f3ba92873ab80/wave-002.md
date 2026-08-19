# Orchestration Wave 2

- Run: `5c52b7f810ad474a9a5f3ba92873ab80`
- Wave: `a48da7ed0b4d4065acdf3c522b988f1b`
- Objective: Fix the confirmed MCP 2026-07-28 stateless cross-tab/default projection leak. Modern stateless requests currently use process-global control_runtime with empty execution_context_id, causing ContextualTaskStateStore and exec_command/task projection to fall back to the global task/run. Implement an application-layer opaque task_context_id carried by tool calls: every modern request must get a nonempty isolated execution scope; supplied task_context_id must deterministically restore the same scope; missing task_context_id must mint a new isolated context rather than inherit global state; strip the common handle before business-tool validation/dispatch as needed; return the handle in modern results so clients can reuse it. Preserve legacy 2025 session behavior, workspace isolation, operator-report latch, accepted unrelated usage_events.py changes, and exactly 8 smart-v3 tools. Do not open P5. Prepare only; no mutation yet.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `0600d799a5f108bd6f2868caab5a4e6bb10c9efdf78a08ab9dd8f68e09f2c54b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20988 | 2026-08-19T08:47:02.726Z | wave_replanned |  | PREFLIGHT | reason=Prior wave was rejected because it performed no source mutation. Changed strategy: inspect the exact current HTTP/schema/test symbols and apply an explicit source patch before running any acceptance proof; do not reuse the prior green baseline proof. |
| 20989 | 2026-08-19T08:47:03.583Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20990 | 2026-08-19T08:48:16.572Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20991 | 2026-08-19T08:48:16.706Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20992 | 2026-08-19T08:48:16.885Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 20993 | 2026-08-19T08:48:17.035Z | state_transition | READY | ROUTED | reason=route_selected |
| 20994 | 2026-08-19T08:48:17.443Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2e3e83afb0684b9b9c4d968d3a2bacca |
| 20995 | 2026-08-19T08:48:17.595Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20996 | 2026-08-19T08:48:18.061Z | patch_surface_observed |  |  |  |
| 20997 | 2026-08-19T08:48:18.220Z | patch_surface_observed |  |  |  |
| 20998 | 2026-08-19T08:48:18.383Z | patch_surface_observed |  |  |  |
| 20999 | 2026-08-19T08:48:18.596Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2e3e83afb0684b9b9c4d968d3a2bacca |
| 21000 | 2026-08-19T08:48:18.758Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21001 | 2026-08-19T08:48:19.088Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=37bc049548b6b5f7f1de33769312a5965f9bc82ed3172a6b53aec71745462ace |
| 21002 | 2026-08-19T08:48:19.394Z | managed_process_admitted |  |  | owner=default |
| 21003 | 2026-08-19T08:48:19.667Z | managed_process_started |  |  | owner=default |
| 21004 | 2026-08-19T08:48:37.647Z | managed_process_terminal |  |  | owner=default |
| 21005 | 2026-08-19T08:48:38.016Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=37bc049548b6b5f7f1de33769312a5965f9bc82ed3172a6b53aec71745462ace |
| 21006 | 2026-08-19T08:48:38.249Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21007 | 2026-08-19T08:48:38.420Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21008 | 2026-08-19T08:48:38.608Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 37bc049548b6b5f7f1de33769312a5965f9bc82ed3172a6b53aec71745462ace | False | 18609 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `25a938ad238fc51fc4cdafb1ad759cf4fd458a4ffe41cde30fb82211eed90cc6`
