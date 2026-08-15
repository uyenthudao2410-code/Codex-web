# Orchestration Wave 1

- Run: `44967efcc20a49a79849a4a55bbffd41`
- Wave: `4b6f23f24a174f4c8afd88d8d897cc50`
- Objective: Complete the OpenCode measurement-integrity fix by correcting only the regression test method boundary. Production attribution/economics behavior remains unchanged from the prior wave.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `9a211ed49c099912959f1be21f1731e57b38e06ccf3b71cc95758e1144ac5db0`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4385 | 2026-08-15T05:06:15.404Z | run_started |  | PREFLIGHT |  |
| 4386 | 2026-08-15T05:06:15.754Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4387 | 2026-08-15T05:06:15.951Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4388 | 2026-08-15T05:06:16.135Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4389 | 2026-08-15T05:06:16.332Z | state_transition | READY | ROUTED | reason=route_selected |
| 4390 | 2026-08-15T05:06:17.011Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8afab41989ef4719969fc88073660d3a |
| 4391 | 2026-08-15T05:06:17.182Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4392 | 2026-08-15T05:06:17.901Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8afab41989ef4719969fc88073660d3a |
| 4393 | 2026-08-15T05:06:18.099Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4394 | 2026-08-15T05:06:18.756Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=1c457cd368af4fef0c975742c409d6ed8f024ab4be8e0079e2ec863aa912c507 |
| 4395 | 2026-08-15T05:06:19.605Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=1c457cd368af4fef0c975742c409d6ed8f024ab4be8e0079e2ec863aa912c507 |
| 4396 | 2026-08-15T05:06:19.846Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=72c1959c038b48cb5331e545cdaab6337b2b4a0131cea994cac567ad96d52f01 |
| 4397 | 2026-08-15T05:06:38.774Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=72c1959c038b48cb5331e545cdaab6337b2b4a0131cea994cac567ad96d52f01 |
| 4398 | 2026-08-15T05:06:39.428Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4399 | 2026-08-15T05:07:24.573Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 1c457cd368af4fef0c975742c409d6ed8f024ab4be8e0079e2ec863aa912c507 | False | 465 | 0 |
| verify:tests | passed | 72c1959c038b48cb5331e545cdaab6337b2b4a0131cea994cac567ad96d52f01 | False | 18547 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fe7e646204f74b69b213be64c921d2c7 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 426519e6b33f3575ddbec8254d60e4427f099f1de0547789e74dbda21b3d695c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `cf87d3b567759aa7e65d6fa2893d057369350b73c06db30a3259f9affc3f94d3`
