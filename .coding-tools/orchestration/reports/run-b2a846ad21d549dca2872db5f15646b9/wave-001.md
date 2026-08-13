# Orchestration Wave 1

- Run: `b2a846ad21d549dca2872db5f15646b9`
- Wave: `ea3bfc2720b04c5bb055bcd6ed92a13f`
- Objective: Add durable idempotency for high-level agent_workflow and deterministic admission/cost budgets without automatic unsafe retries. Same idempotency key+request hash must deduplicate across Runtime recreation; conflicting reuse must fail; in-progress records from a prior process become outcome-unknown and must not auto-replay; compact summaries only. Admission must bound planned auto steps/tool hops/runtime and optionally candidate estimated credits. Keep 8 smart tools and all current transport/fencing/Codex behavior. Do not commit or push.
- Mode: `mcp_only`
- Base HEAD: `a051897449827e4753b16def1b693d867fad76e9`
- Worktree fingerprint: `73e921f56bd344f06ea0a85490b385f60bb7e34ce45f3f706d07c053fc4c15f1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 370 | 2026-08-13T09:32:24.269Z | run_started |  | PREFLIGHT |  |
| 371 | 2026-08-13T09:32:24.601Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 372 | 2026-08-13T09:32:24.808Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 373 | 2026-08-13T09:32:24.987Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 374 | 2026-08-13T09:32:25.216Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 375 | 2026-08-13T09:32:25.424Z | state_transition | READY | ROUTED | reason=route_selected |
| 376 | 2026-08-13T09:32:25.914Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=847d2642d6a2435a916c4e1f9552b6b4 |
| 377 | 2026-08-13T09:32:26.123Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 378 | 2026-08-13T09:32:26.789Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=847d2642d6a2435a916c4e1f9552b6b4 |
| 379 | 2026-08-13T09:32:26.977Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 380 | 2026-08-13T09:32:31.410Z | proof_recorded |  |  | stage_id=check:972a3720579c7aaf; status=passed; cache_hit=False; input_fingerprint=0ccd4795ba6f95fe467856a7e28e918984ad16e3d6074a0ee61d357a0ec8f340 |
| 381 | 2026-08-13T09:32:32.110Z | proof_recorded |  |  | stage_id=check:a8aff4737c6ce2c3; status=passed; cache_hit=False; input_fingerprint=51ec4c484bc840a0cd1327521ef2fe5164b99d2144376d8120fc840cef0f2855 |
| 382 | 2026-08-13T09:32:32.513Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 383 | 2026-08-13T09:32:54.809Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:972a3720579c7aaf | passed | 0ccd4795ba6f95fe467856a7e28e918984ad16e3d6074a0ee61d357a0ec8f340 | False | 3435 | 0 |
| check:a8aff4737c6ce2c3 | passed | 51ec4c484bc840a0cd1327521ef2fe5164b99d2144376d8120fc840cef0f2855 | False | 289 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 0f7c8437d45742ad9d8d4877ddebb874 | accepted | a051897449827e4753b16def1b693d867fad76e9 | 9d88dcfe3be333c8c1e49028db3a6d1ae5cda30d65b2fdd7fbee69f73f5a3924 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `03d24b173077ce9eb1435af9e00df819afae4f4f75dfd3c70a1c92b62bacbe82`
