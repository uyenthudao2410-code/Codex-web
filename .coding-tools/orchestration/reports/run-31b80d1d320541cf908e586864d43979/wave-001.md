# Orchestration Wave 1

- Run: `31b80d1d320541cf908e586864d43979`
- Wave: `5c3eccab8737482bba7f01bfe304c25f`
- Objective: Add an OpenCode-only compatibility mode to the existing hub_proxy_stdio so OpenCode models can consume Coding Tools MCP structuredContent. Preserve Codex Desktop default behavior and the 8-tool public contract. Inspect only the proxy, its focused tests, and opencode.json. No writes in prepare.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `77cf91225520e82891bf1d8e03743334bdc5a5e8777b48e8186ed455ba5a80c1`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1427 | 2026-08-14T06:47:49.452Z | run_started |  | PREFLIGHT |  |
| 1428 | 2026-08-14T06:47:50.865Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1429 | 2026-08-14T06:48:25.896Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 1430 | 2026-08-14T06:48:26.073Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1431 | 2026-08-14T06:48:26.271Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1432 | 2026-08-14T06:48:26.458Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1433 | 2026-08-14T06:48:26.681Z | state_transition | READY | ROUTED | reason=route_selected |
| 1434 | 2026-08-14T06:48:27.819Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0037d037dc0248e5aa06dddb81e45546 |
| 1435 | 2026-08-14T06:48:28.006Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1436 | 2026-08-14T06:48:28.910Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0037d037dc0248e5aa06dddb81e45546 |
| 1437 | 2026-08-14T06:48:29.116Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1438 | 2026-08-14T06:48:35.836Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=526df6e84c9c4b7620922cc7aa1ab6b52aaed1962a404938f293b6c43c1d4038 |
| 1439 | 2026-08-14T06:48:36.358Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1440 | 2026-08-14T06:51:07.381Z | failure_observed | ACCEPTING | ACCEPTING | reason=Live OpenCode canary failed with MCP -32600 because outputSchema validation requires structuredContent to remain present. Replan compatibility mode to preserve structuredContent for SDK/schema validation while mirroring its JSON into the first text content block for model visibility; keep this opt-in only for OpenCode.; failure_class=SOL_REJECTED |
| 1441 | 2026-08-14T06:51:07.592Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 526df6e84c9c4b7620922cc7aa1ab6b52aaed1962a404938f293b6c43c1d4038 | False | 5875 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `ef0a68d8c06154f8b26f31494f1d609f9b638b261acd4344b5459037950e22b6`
