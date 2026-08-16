# Orchestration Wave 1

- Run: `24a33f298dfe40d2ba45ef973c78b2f8`
- Wave: `19feb6feb18a4cecacffb9e3fc2a4345`
- Objective: Harden the existing P2/P3 durability repair with a real restart regression proof, without changing runtime behavior unless the regression exposes a failure. The current worktree already contains the intended P2/P3 semantic and control-plane source changes. Modify only resources/coding-tools-mcp/tests/test_orchestration_workflow.py so test_reconnect_repairs_acceptance_projection_from_ledger actually closes the first Runtime, constructs a fresh Runtime against the same workspace/ledger, and verifies startup reconciliation restores the ACCEPTING projection and Awaiting acceptance task state. Preserve all unrelated dirty files. Then verify the current intended P2/P3 worktree with the focused coordination/orchestration and semantic/runtime Python suites, scoped rustfmt, the native semantic concurrency Rust regression, and git diff --check. Do not edit SQLite directly, do not restart runtime in this wave, do not touch credentials, do not commit or push.
- Mode: `mcp_only`
- Base HEAD: `64ac538ae374965bf8d51428f4b4508363b79f2f`
- Worktree fingerprint: `2e8ac048a4d9056a03127083217fd41c545d7fa06bb446eab11e03b029e6a36a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5579 | 2026-08-16T00:36:28.695Z | run_started |  | PREFLIGHT |  |
| 5580 | 2026-08-16T00:36:29.054Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 5581 | 2026-08-16T00:36:29.198Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5582 | 2026-08-16T00:36:29.285Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5583 | 2026-08-16T00:36:29.414Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5584 | 2026-08-16T00:36:29.526Z | state_transition | READY | ROUTED | reason=route_selected |
| 5585 | 2026-08-16T00:36:29.892Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6743dfb15ace4aaa925cbbd618c40ea7 |
| 5586 | 2026-08-16T00:36:30.007Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5587 | 2026-08-16T00:36:30.419Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6743dfb15ace4aaa925cbbd618c40ea7 |
| 5588 | 2026-08-16T00:36:30.553Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5589 | 2026-08-16T00:36:30.876Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=662cdd74d64fa9fb83e50578dcf7f42ef79cf9811b5ffb537adea221d63a6fb7 |
| 5590 | 2026-08-16T00:36:40.235Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=662cdd74d64fa9fb83e50578dcf7f42ef79cf9811b5ffb537adea221d63a6fb7 |
| 5591 | 2026-08-16T00:36:40.664Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5592 | 2026-08-16T00:37:13.156Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 662cdd74d64fa9fb83e50578dcf7f42ef79cf9811b5ffb537adea221d63a6fb7 | False | 9109 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5e672d1db1234e5ebeef591f687fc7d9 | accepted | 64ac538ae374965bf8d51428f4b4508363b79f2f | b3b15fb4ef88a2ae239681eee085b44b2f639cebb1c6437453fdb91f68f77c1c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `a5437989e7c6add3474bd0b79f9d57a79302c171f26fa5e19d59432d3a2b7d23`
