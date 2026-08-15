# Orchestration Wave 1

- Run: `cabac3c58fdd4de1a0f43075c28d4c08`
- Wave: `ddb2879ffb634b8e87fce2fd90aa556b`
- Objective: Remove evaluation window bias without weakening normal history caps. paired_policy_evaluation must scan up to its declared bounded limit (max 500) directly from the durable ledger instead of calling list_runs(), whose UI/history safety cap is 100. Report scanned_runs explicitly and classify zero-pair Pareto state as indeterminate_no_pairs. Preserve all routing/cost-control behavior and do not call providers.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `3f2657ffd7dae864506917c025f0deeec21c9be30b65a071e1c7795578ffffe4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4179 | 2026-08-15T04:24:15.213Z | run_started |  | PREFLIGHT |  |
| 4180 | 2026-08-15T04:24:15.472Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4181 | 2026-08-15T04:24:15.717Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4182 | 2026-08-15T04:24:15.886Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4183 | 2026-08-15T04:24:16.087Z | state_transition | READY | ROUTED | reason=route_selected |
| 4184 | 2026-08-15T04:24:16.670Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5f6bcc1b326e43678e3b63f068a312af |
| 4185 | 2026-08-15T04:24:16.936Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4186 | 2026-08-15T04:24:17.524Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5f6bcc1b326e43678e3b63f068a312af |
| 4187 | 2026-08-15T04:24:17.720Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4188 | 2026-08-15T04:24:18.173Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5aef5a7e7f246bf0d723b13c1b69012d84cd5e0d716e5eb011b344dbf5b4ef10 |
| 4189 | 2026-08-15T04:24:34.736Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5aef5a7e7f246bf0d723b13c1b69012d84cd5e0d716e5eb011b344dbf5b4ef10 |
| 4190 | 2026-08-15T04:24:35.272Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4191 | 2026-08-15T04:24:46.708Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 5aef5a7e7f246bf0d723b13c1b69012d84cd5e0d716e5eb011b344dbf5b4ef10 | False | 16188 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 12bf39c95d4f429cad2117d461f51f51 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 911f5b1b5031cef4ea05e2ec9f8b8138d3c52844a349eca96c9730ed3f175340 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `777ab7d4087739346815b7f03cb0e1129d93b85fd44980c75f60b421778fe44d`
