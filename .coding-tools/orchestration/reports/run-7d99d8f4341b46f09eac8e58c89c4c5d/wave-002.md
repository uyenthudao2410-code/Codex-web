# Orchestration Wave 2

- Run: `7d99d8f4341b46f09eac8e58c89c4c5d`
- Wave: `36b2f6e65c214e168673d5b46fefb2d0`
- Objective: Implement Execution Hub server/runtime integration without changing the public smart-v3 8-tool input contract. Add authenticated logical client identity/heartbeat, default ChatWeb controller claim only when unowned/expired, renewal without stealing, per-client observed-event cursors, controller enforcement for HTTP accept/reject, internal /__control/hub heartbeat+operator transfer, and orchestration snapshot schema v2 with clients/authority/continuity/bounded resume packet and conservative SAFE_TO_ROTATE_CHATWEB. Preserve all existing P1.5 behavior and old snapshot keys.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `ca7d7483616234481d8cd13b42923a094941f64f3267177abd6cf2e5b3d1ab4f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 964 | 2026-08-14T05:13:41.103Z | wave_replanned |  | PREFLIGHT | reason=The first focused proof had 12 passes and one failure because the new test Runtime inherited the repository default `coding` tool mode, where task_control is intentionally not exposed. The HTTP status was 200 with JSON-RPC unknown_tool. Set CODING_TOOLS_MCP_TOOL_MODE=smart for the isolated test Runtime and assert no JSON-RPC error before reading structuredContent. |
| 965 | 2026-08-14T05:13:41.265Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 966 | 2026-08-14T05:13:41.428Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 967 | 2026-08-14T05:13:41.622Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 968 | 2026-08-14T05:13:41.797Z | state_transition | READY | ROUTED | reason=route_selected |
| 969 | 2026-08-14T05:13:42.341Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5607436ad2c14d4585c98f9abf313128 |
| 970 | 2026-08-14T05:13:42.487Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 971 | 2026-08-14T05:13:43.098Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5607436ad2c14d4585c98f9abf313128 |
| 972 | 2026-08-14T05:13:43.261Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 973 | 2026-08-14T05:13:49.627Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=77cd53ccb3cde337c080d551136a3c2e768a2bd39c386cae5ad4ae55035fd2f3 |
| 974 | 2026-08-14T05:13:49.798Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 975 | 2026-08-14T05:13:49.996Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 77cd53ccb3cde337c080d551136a3c2e768a2bd39c386cae5ad4ae55035fd2f3 | False | 5750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `59`
- Chain head: `08214eaddbe2e4d9545cc957198c45abb82406e7bc77e26c1e20d012244223b7`
