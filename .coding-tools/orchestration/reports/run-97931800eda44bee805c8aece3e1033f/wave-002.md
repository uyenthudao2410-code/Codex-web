# Orchestration Wave 2

- Run: `97931800eda44bee805c8aece3e1033f`
- Wave: `ce3b69eda5cf413a9d9fe18282063ec4`
- Objective: Fix EOCL terminal completion-report ACK self-lock: read-only orchestration projections with write_reports=False must not overwrite the durable completion-report latch or clear an existing ACK. Add regression proving accepted terminal report -> ACK -> task_control audit preserves the same acknowledged durable report and leaves no pending operator report.
- Objective revision: `2`
- Objective SHA-256: `bc7710712d69f421813b2a37e2b89c0d9281878c20050abec3c7b2b6c1b8f846`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `4ae3f16839b70d7bc54692152a6c9298ce02c9e9a9c9d16fabfabdd2cfe9b6dd`
- Contract fingerprint: `4473f19f83a005a4520c956de77cd3e6602bf72bd29900231f5d7bcb222f456a`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26319 | 2026-08-21T16:54:12.389Z | wave_replanned |  | PREFLIGHT | reason=Refreshed preflight evidence identified the exact non-interference defect: read-only orchestration projection calls build_orchestration_runtime_result(write_reports=False), yet operator_report.py still persists that derived report through set_completion_report(), changing the report digest and re-arming ACK. Replan is limited to guarding that persistence plus one focused regression; no scope expansion. |
| 26320 | 2026-08-21T16:54:12.564Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26321 | 2026-08-21T16:54:12.742Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26322 | 2026-08-21T16:54:12.902Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26323 | 2026-08-21T16:54:13.100Z | state_transition | READY | ROUTED | reason=route_selected |
| 26324 | 2026-08-21T16:54:13.519Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cecbd154130c48a8aa89ae9f61264fd2 |
| 26325 | 2026-08-21T16:54:13.734Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26326 | 2026-08-21T16:54:14.226Z | patch_surface_observed |  |  |  |
| 26327 | 2026-08-21T16:54:14.473Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cecbd154130c48a8aa89ae9f61264fd2 |
| 26328 | 2026-08-21T16:54:14.674Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26329 | 2026-08-21T16:54:15.084Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9cc590fd60cc32b6bf43c6c0aff7312d4d1b6a978cb2a0d08d94c212d883e78f |
| 26330 | 2026-08-21T16:54:15.465Z | managed_process_admitted |  |  | owner=default |
| 26331 | 2026-08-21T16:54:15.835Z | managed_process_started |  |  | owner=default |
| 26332 | 2026-08-21T16:54:21.247Z | managed_process_terminal |  |  | owner=default |
| 26333 | 2026-08-21T16:54:22.737Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9cc590fd60cc32b6bf43c6c0aff7312d4d1b6a978cb2a0d08d94c212d883e78f |
| 26334 | 2026-08-21T16:54:23.301Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 26335 | 2026-08-21T20:27:28.718Z | quality_outcome_recorded |  |  |  |
| 26336 | 2026-08-21T20:27:28.883Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 26337 | 2026-08-21T20:27:29.238Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 9cc590fd60cc32b6bf43c6c0aff7312d4d1b6a978cb2a0d08d94c212d883e78f | False | 7203 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 315b3bab8e7c4eb1bf8a58d7f702a8cc | accepted | 9eb05072e54ffca9576e23c2d4a4f4e14034bddc | acc2f3333bf0d8cffd9ae509cd5711986ddfa6d3e3e7bb624fca8819faf894e1 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `91d8f90c113403e39fbfee1e99f2aa47cb9bb21ed5b3692600189c0e0e4deb65`
