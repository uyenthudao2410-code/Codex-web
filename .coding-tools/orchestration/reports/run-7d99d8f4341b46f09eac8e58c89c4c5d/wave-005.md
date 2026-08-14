# Orchestration Wave 5

- Run: `7d99d8f4341b46f09eac8e58c89c4c5d`
- Wave: `8f891070eb24454f83d6df8b4ade7688`
- Objective: Implement Execution Hub server/runtime integration without changing the public smart-v3 8-tool input contract. Add authenticated logical client identity/heartbeat, default ChatWeb controller claim only when unowned/expired, renewal without stealing, per-client observed-event cursors, controller enforcement for HTTP accept/reject, internal /__control/hub heartbeat+operator transfer, and orchestration snapshot schema v2 with clients/authority/continuity/bounded resume packet and conservative SAFE_TO_ROTATE_CHATWEB. Preserve all existing P1.5 behavior and old snapshot keys.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `19ea90c9abb0efd3389e1952d2f450deb18987f35807bc7bf237cab79e2228f4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 999 | 2026-08-14T05:15:32.836Z | wave_replanned |  | PREFLIGHT | reason=Diagnostic proof identified the only remaining reason as CAPSULE_STALE. Root cause is comparing capsule.created_at to generic task-state updated_at, which is not an execution-state oracle. Replace it with durable orchestration event comparison, excluding control-only controller transfer and write-lease renewal events that are projected live separately. |
| 1000 | 2026-08-14T05:15:33.013Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1001 | 2026-08-14T05:15:33.253Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1002 | 2026-08-14T05:15:33.443Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1003 | 2026-08-14T05:15:33.617Z | state_transition | READY | ROUTED | reason=route_selected |
| 1004 | 2026-08-14T05:15:34.289Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=fe0c619312c143c4a457036e4a7e534b |
| 1005 | 2026-08-14T05:15:34.462Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1006 | 2026-08-14T05:15:35.256Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=fe0c619312c143c4a457036e4a7e534b |
| 1007 | 2026-08-14T05:15:35.421Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1008 | 2026-08-14T05:15:43.596Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=eb53ce2ab52471fc770cf19cd2107c5b12b7b07d4ab15b2331362ebc84a87dec |
| 1009 | 2026-08-14T05:15:44.031Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1010 | 2026-08-14T05:16:02.316Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | eb53ce2ab52471fc770cf19cd2107c5b12b7b07d4ab15b2331362ebc84a87dec | False | 7484 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 01d6017c94044d6497588ef69f667e99 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | df4077e9c75546000fddb04aaf3c86f9df92d7cc8403b7b6ec17a7cc3e0f5e6b | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `59`
- Chain head: `08214eaddbe2e4d9545cc957198c45abb82406e7bc77e26c1e20d012244223b7`
