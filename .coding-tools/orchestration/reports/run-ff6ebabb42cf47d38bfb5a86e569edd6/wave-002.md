# Orchestration Wave 2

- Run: `ff6ebabb42cf47d38bfb5a86e569edd6`
- Wave: `0148c4a8438347c49f50b3d81eb27107`
- Objective: Prepare a one-time fail-closed migration repair for the pre-fix running Coding MCP. Inspect only resources/coding-tools-mcp/scripts/reconcile_execution_resources.py and its focused tests (or nearest execution-resource script tests). Determine the smallest change to (1) include sanitized command_id and owner in remaining active-row diagnostics, and (2) add an explicit opt-in repair flag that can terminate only one live runtime-owned Codex App Server sidecar when its durable managed row strictly matches owner=codex-app-server, command_id prefix codex-app-server-, MEDIUM, empty run_id/wave_id, active lifecycle, PID identity token still matches, and no other non-self active managed work exists. The repair must refuse on ambiguity/mismatch, never terminate arbitrary PID, then reconcile and verify the row terminalized. No writes in prepare.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `e10f58cb61056df413e0a5c3b435bd4fe4ebc445d5317d95e292e30a720a1323`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8702 | 2026-08-16T14:27:09.657Z | wave_replanned |  | PREFLIGHT | reason=The prepare snapshot became stale because concurrent runtime/worktree evidence changed before execution. No prior mutation occurred. Replan with the same two-file bounded repair design using the just-read current script and fail-closed identity requirements; preserve all unrelated changes. |
| 8703 | 2026-08-16T14:27:09.792Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8704 | 2026-08-16T14:27:09.924Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8705 | 2026-08-16T14:27:10.056Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8706 | 2026-08-16T14:27:10.150Z | state_transition | READY | ROUTED | reason=route_selected |
| 8707 | 2026-08-16T14:27:10.588Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5a7e0191dd0b4df7b95ac38146a0c72f |
| 8708 | 2026-08-16T14:27:10.707Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8709 | 2026-08-16T14:27:11.190Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5a7e0191dd0b4df7b95ac38146a0c72f |
| 8710 | 2026-08-16T14:27:11.289Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8711 | 2026-08-16T14:27:11.638Z | proof_cache_miss |  |  | reason=cold; stage_id=check:362784afd3165f5c; input_fingerprint=ee717e58047abb9e00d58dc4c870d7a2105ad513be5127012df13f12d48134ab |
| 8712 | 2026-08-16T14:27:11.934Z | managed_process_admitted |  |  | owner=default |
| 8713 | 2026-08-16T14:27:12.131Z | managed_process_started |  |  | owner=default |
| 8714 | 2026-08-16T14:27:12.471Z | managed_process_terminal |  |  | owner=default |
| 8715 | 2026-08-16T14:27:12.686Z | proof_recorded |  |  | stage_id=check:362784afd3165f5c; status=passed; cache_hit=False; input_fingerprint=ee717e58047abb9e00d58dc4c870d7a2105ad513be5127012df13f12d48134ab |
| 8716 | 2026-08-16T14:27:12.814Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5fa0ca4051c8cc61; input_fingerprint=9ee91e1415996b34628866013a93c30fb842449ea64af371e0160ee21927e105 |
| 8717 | 2026-08-16T14:27:13.100Z | managed_process_admitted |  |  | owner=default |
| 8718 | 2026-08-16T14:27:13.301Z | managed_process_started |  |  | owner=default |
| 8719 | 2026-08-16T14:27:14.450Z | managed_process_terminal |  |  | owner=default |
| 8720 | 2026-08-16T14:27:14.673Z | proof_recorded |  |  | stage_id=check:5fa0ca4051c8cc61; status=passed; cache_hit=False; input_fingerprint=9ee91e1415996b34628866013a93c30fb842449ea64af371e0160ee21927e105 |
| 8721 | 2026-08-16T14:27:15.250Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8722 | 2026-08-16T14:28:02.699Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8723 | 2026-08-16T14:28:02.985Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:362784afd3165f5c | passed | ee717e58047abb9e00d58dc4c870d7a2105ad513be5127012df13f12d48134ab | False | 805 | 0 |
| check:5fa0ca4051c8cc61 | passed | 9ee91e1415996b34628866013a93c30fb842449ea64af371e0160ee21927e105 | False | 1627 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 554b4ccff8aa4318b4ef2c704767ef29 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 9b088f9f1cd69d4da232ddea4639b6e22365a60e118735c79e2d7d1183fcf966 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `74c4b55b905246b8a5d1d50b0432262734ea3a5dc23b813cea7774271206de3c`
