# Orchestration Wave 3

- Run: `fd693ed40c41493283b83ece23bb4eb6`
- Wave: `27744d551a6343de864b3ea6fa9d58d3`
- Objective: Add focused Execution Hub fault/E2E release tests only. Prove: ChatWeb and Codex Desktop logical identities use one shared HTTP Runtime/ledger while keeping independent cursors; Desktop cannot steal a live ChatWeb controller but explicit transfer increments fencing and stale ChatWeb semantic acceptance is rejected; an initialized authenticated MCP session id from Runtime A is accepted as an alias after Runtime A stops and Runtime B starts on the same workspace, while durable task/run/capsule survive and the response rotates to Runtime B's session id. Do not change production code unless the test exposes a real defect.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `8be505634b8771de9971a1628564afbe993fd795bb0a1eb77697d7c8646b2a3c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1173 | 2026-08-14T05:38:52.026Z | wave_replanned |  | PREFLIGHT | reason=Second fault run leaves one production defect and one expectation mismatch. Production defect: HTTPSessionManager.get intentionally aliases an authenticated old session id to the new shared Runtime, but handler does not mark that freshly recreated Runtime initialized, causing `Server not initialized`. Existing compatibility paths already allow authenticated tools/list/tools/call to initialize a shared Runtime without a fresh initialize request, so apply the same bounded initialization only when alias-target Runtime is currently uninitialized, then keep the protocol-version check. The Desktop acceptance path correctly returns typed FINAL_ACCEPTANCE_NOT_READY after controller fencing succeeds; update the test code only for that stable typed result. |
| 1174 | 2026-08-14T05:38:52.201Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1175 | 2026-08-14T05:38:52.413Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1176 | 2026-08-14T05:38:52.627Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1177 | 2026-08-14T05:38:52.825Z | state_transition | READY | ROUTED | reason=route_selected |
| 1178 | 2026-08-14T05:38:53.378Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=002c4ab9148e400f867150968362ad4b |
| 1179 | 2026-08-14T05:38:53.552Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1180 | 2026-08-14T05:38:54.228Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=002c4ab9148e400f867150968362ad4b |
| 1181 | 2026-08-14T05:38:54.400Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1182 | 2026-08-14T05:39:04.778Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=4a12d2e278af20b020c93c6a02aa3d020d75a4a982ff4e8e07bb12177ba47ee8 |
| 1183 | 2026-08-14T05:39:05.122Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1184 | 2026-08-14T05:39:23.208Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 4a12d2e278af20b020c93c6a02aa3d020d75a4a982ff4e8e07bb12177ba47ee8 | False | 9750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fda16dc2bbe74f36bd570b8169b43999 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 528e9155bd53ea86718bde388d2450e7b432d53eaaa1c47ac32988c0ae27bcb2 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `13f5e9d955cd4233e4a623d935e01445a670549a793123781103d28477da3877`
