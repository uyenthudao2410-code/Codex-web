# Orchestration Wave 1

- Run: `5529f06801224f6297d2d2e76da8a351`
- Wave: `8a83a3d429a140d9b4b0a86e2c1af7ed`
- Objective: Check whether Cockpit is dynamically rewriting Codex config after account switch: report config last-write timestamp, active model_provider, and count of base_url entries only. No secrets, no mutation.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `58e23cb3137ed277ca2fafb9a8b87de92f4d890df487e3696ee00097ade6781f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4768 | 2026-08-15T07:44:33.406Z | run_started |  | PREFLIGHT |  |
| 4769 | 2026-08-15T07:44:34.322Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4770 | 2026-08-15T07:44:34.870Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 4771 | 2026-08-15T07:44:35.165Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4772 | 2026-08-15T07:44:35.422Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4773 | 2026-08-15T07:44:35.652Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4774 | 2026-08-15T07:44:36.193Z | state_transition | READY | ROUTED | reason=route_selected |
| 4775 | 2026-08-15T07:44:37.166Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cf265d4123f8438ab1647b26f84f3ec3 |
| 4776 | 2026-08-15T07:44:37.343Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4777 | 2026-08-15T07:44:38.253Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cf265d4123f8438ab1647b26f84f3ec3 |
| 4778 | 2026-08-15T07:44:38.555Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4779 | 2026-08-15T07:44:39.383Z | proof_cache_miss |  |  | reason=cold; stage_id=check:db86de40d9db318c; input_fingerprint=77309da331f9625c84dc49b98ed6fef9bcd0f7f5c3a796f59a677541b4931cd5 |
| 4780 | 2026-08-15T07:44:41.062Z | proof_recorded |  |  | stage_id=check:db86de40d9db318c; status=passed; cache_hit=False; input_fingerprint=77309da331f9625c84dc49b98ed6fef9bcd0f7f5c3a796f59a677541b4931cd5 |
| 4781 | 2026-08-15T07:44:41.343Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4782 | 2026-08-15T07:44:50.294Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:db86de40d9db318c | passed | 77309da331f9625c84dc49b98ed6fef9bcd0f7f5c3a796f59a677541b4931cd5 | False | 1187 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| af3d839285304d8b8b9974f6b5dadc16 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 208e2d7ee88336af2eb7352b96e65babcfa0452e74242c8d6c9feab00437abb1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `f457ac5850a23db6f0f24d7ef71690605f63c5f63eb2d2178625c8bb0b712064`
