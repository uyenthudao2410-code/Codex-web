# Orchestration Wave 1

- Run: `fd693ed40c41493283b83ece23bb4eb6`
- Wave: `53b82fb4575a4581a20c31e04bbd5121`
- Objective: Add focused Execution Hub fault/E2E release tests only. Prove: ChatWeb and Codex Desktop logical identities use one shared HTTP Runtime/ledger while keeping independent cursors; Desktop cannot steal a live ChatWeb controller but explicit transfer increments fencing and stale ChatWeb semantic acceptance is rejected; an initialized authenticated MCP session id from Runtime A is accepted as an alias after Runtime A stops and Runtime B starts on the same workspace, while durable task/run/capsule survive and the response rotates to Runtime B's session id. Do not change production code unless the test exposes a real defect.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `0b39ce46489a8958931592017730323d266ad9e4b6b348eb40e8e34637a10b6a`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1148 | 2026-08-14T05:36:28.333Z | run_started |  | PREFLIGHT |  |
| 1149 | 2026-08-14T05:36:28.797Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1150 | 2026-08-14T05:36:28.971Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1151 | 2026-08-14T05:36:29.151Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1152 | 2026-08-14T05:36:29.333Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1153 | 2026-08-14T05:36:29.516Z | state_transition | READY | ROUTED | reason=route_selected |
| 1154 | 2026-08-14T05:36:30.066Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f2573b4db10e4e5b8b12f0eac78c3447 |
| 1155 | 2026-08-14T05:36:30.310Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1156 | 2026-08-14T05:36:30.883Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f2573b4db10e4e5b8b12f0eac78c3447 |
| 1157 | 2026-08-14T05:36:31.082Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1158 | 2026-08-14T05:36:41.066Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=f4c88080207c6b6afcc8ec9ccf6ae6b72eb7f37d7aa70635a0605cd753e624a4 |
| 1159 | 2026-08-14T05:36:41.265Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 1160 | 2026-08-14T05:36:41.483Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | f4c88080207c6b6afcc8ec9ccf6ae6b72eb7f37d7aa70635a0605cd753e624a4 | False | 9343 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `13f5e9d955cd4233e4a623d935e01445a670549a793123781103d28477da3877`
