# Orchestration Wave 1

- Run: `5c52b7f810ad474a9a5f3ba92873ab80`
- Wave: `0e5d45be106347178bda384eb43513ec`
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
| 20965 | 2026-08-19T08:43:16.553Z | run_started |  | PREFLIGHT |  |
| 20966 | 2026-08-19T08:43:17.272Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20967 | 2026-08-19T08:43:36.244Z | solution_shadow_recommended |  |  |  |
| 20968 | 2026-08-19T08:44:53.334Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20969 | 2026-08-19T08:44:53.477Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20970 | 2026-08-19T08:44:53.604Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 20971 | 2026-08-19T08:44:53.802Z | state_transition | READY | ROUTED | reason=route_selected |
| 20972 | 2026-08-19T08:44:54.305Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=52859c1158b5415aa41e8542af0541d0 |
| 20973 | 2026-08-19T08:44:54.467Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20974 | 2026-08-19T08:44:54.962Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=52859c1158b5415aa41e8542af0541d0 |
| 20975 | 2026-08-19T08:44:55.143Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20976 | 2026-08-19T08:44:55.478Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=cd271bdca059f9523e078bce65ee42c33c7a28b79d9e6398fba450528622fe03 |
| 20977 | 2026-08-19T08:44:55.862Z | managed_process_admitted |  |  | owner=default |
| 20978 | 2026-08-19T08:44:56.114Z | managed_process_started |  |  | owner=default |
| 20979 | 2026-08-19T08:45:13.225Z | managed_process_terminal |  |  | owner=default |
| 20980 | 2026-08-19T08:45:13.569Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=cd271bdca059f9523e078bce65ee42c33c7a28b79d9e6398fba450528622fe03 |
| 20981 | 2026-08-19T08:45:13.909Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 20982 | 2026-08-19T08:45:29.305Z | managed_process_admitted |  |  | owner=default |
| 20983 | 2026-08-19T08:45:29.564Z | managed_process_started |  |  | owner=default |
| 20984 | 2026-08-19T08:45:30.038Z | managed_process_terminal |  |  | owner=default |
| 20985 | 2026-08-19T08:45:41.923Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject no-op proof: focused tests passed but agent_workflow reported affected_files=[] and patch_results=[], and an explicit git diff of mcp_http_handler.py, tool_schema.py, and test_stateless_http_2026.py is empty. The confirmed stateless global-projection bug is therefore still unfixed. Replan must apply an explicit source patch before re-running proof; do not reuse proof 88a4e54872274bd7983bbeb5a4254d90 as acceptance evidence.; failure_class=SOL_REJECTED |
| 20986 | 2026-08-19T08:45:42.103Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 20987 | 2026-08-19T08:45:42.276Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | cd271bdca059f9523e078bce65ee42c33c7a28b79d9e6398fba450528622fe03 | False | 17780 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `25a938ad238fc51fc4cdafb1ad759cf4fd458a4ffe41cde30fb82211eed90cc6`
