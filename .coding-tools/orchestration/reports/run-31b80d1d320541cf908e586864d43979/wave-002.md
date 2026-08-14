# Orchestration Wave 2

- Run: `31b80d1d320541cf908e586864d43979`
- Wave: `1b0bbed1448d4ed3a64574c3e8174ef2`
- Objective: Add an OpenCode-only compatibility mode to the existing hub_proxy_stdio so OpenCode models can consume Coding Tools MCP structuredContent. Preserve Codex Desktop default behavior and the 8-tool public contract. Inspect only the proxy, its focused tests, and opencode.json. No writes in prepare.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `3d605feb7988ad7fafca78a75a3412d6c27335da9c31dabb696fd37fa750cdc6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1442 | 2026-08-14T06:51:22.401Z | wave_replanned |  | PREFLIGHT | reason=Live OpenCode canary proved that removing structuredContent violates the tool outputSchema and OpenCode rejects the result with MCP -32600 before the model sees the text. The new strategy preserves canonical structuredContent for schema validation and mirrors it into text only for OpenCode model visibility. |
| 1443 | 2026-08-14T06:51:22.582Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1444 | 2026-08-14T06:51:22.751Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1445 | 2026-08-14T06:51:23.210Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1446 | 2026-08-14T06:51:23.494Z | state_transition | READY | ROUTED | reason=route_selected |
| 1447 | 2026-08-14T06:51:24.152Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d7dbad10e1c645ac90bbb28a11222b46 |
| 1448 | 2026-08-14T06:51:24.378Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1449 | 2026-08-14T06:51:25.243Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d7dbad10e1c645ac90bbb28a11222b46 |
| 1450 | 2026-08-14T06:51:25.442Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1451 | 2026-08-14T06:51:32.408Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=8e44fcc5b759afa11761bfa502f1eff09d0a34004b8404135f22bd13bd85fa34 |
| 1452 | 2026-08-14T06:51:32.777Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1453 | 2026-08-14T06:53:52.657Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 8e44fcc5b759afa11761bfa502f1eff09d0a34004b8404135f22bd13bd85fa34 | False | 6125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 01687830a5184c90a872a831492aa204 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | d1af3df5865d973541bddce1f723848b2cf75e6adc56367f760c0941a71e2a46 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `ef0a68d8c06154f8b26f31494f1d609f9b638b261acd4344b5459037950e22b6`
