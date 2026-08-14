# Orchestration Wave 2

- Run: `fd693ed40c41493283b83ece23bb4eb6`
- Wave: `43951ac93c4544e38fa89efea2059e5e`
- Objective: Add focused Execution Hub fault/E2E release tests only. Prove: ChatWeb and Codex Desktop logical identities use one shared HTTP Runtime/ledger while keeping independent cursors; Desktop cannot steal a live ChatWeb controller but explicit transfer increments fencing and stale ChatWeb semantic acceptance is rejected; an initialized authenticated MCP session id from Runtime A is accepted as an alias after Runtime A stops and Runtime B starts on the same workspace, while durable task/run/capsule survive and the response rotates to Runtime B's session id. Do not change production code unless the test exposes a real defect.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e2ba5e2989be46df1ae979f8035293e941390813bd1bed5f7002ab4b209d798d`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1161 | 2026-08-14T05:37:25.901Z | wave_replanned |  | PREFLIGHT | reason=Initial fault proof produced 2 failures with 16 passes. Source inspection shows both are test assumptions: task_control get wraps TaskState under `state`; process_instance_id is generated once per Python process, so two Runtime objects in one test process share it by design. Preserve the strong checks on shared task truth, independent cursors, controller fencing, changed server_instance_id, old session alias acceptance, new returned session id, and durable run/capsule across server recreation. |
| 1162 | 2026-08-14T05:37:26.114Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1163 | 2026-08-14T05:37:26.302Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1164 | 2026-08-14T05:37:26.494Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1165 | 2026-08-14T05:37:26.681Z | state_transition | READY | ROUTED | reason=route_selected |
| 1166 | 2026-08-14T05:37:27.245Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4cb27d94da804d57908383c58ad1d976 |
| 1167 | 2026-08-14T05:37:27.420Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1168 | 2026-08-14T05:37:28.012Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4cb27d94da804d57908383c58ad1d976 |
| 1169 | 2026-08-14T05:37:28.229Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1170 | 2026-08-14T05:37:38.676Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=46a41c3fb6b23fdc04ed9e022a04be8e401f513069aeeb9c8c9b55eb7ba94be2 |
| 1171 | 2026-08-14T05:37:38.863Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 1172 | 2026-08-14T05:37:39.028Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 46a41c3fb6b23fdc04ed9e022a04be8e401f513069aeeb9c8c9b55eb7ba94be2 | False | 9875 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `13f5e9d955cd4233e4a623d935e01445a670549a793123781103d28477da3877`
