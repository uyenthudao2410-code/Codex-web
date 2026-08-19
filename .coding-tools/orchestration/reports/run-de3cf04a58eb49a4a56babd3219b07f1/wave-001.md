# Orchestration Wave 1

- Run: `de3cf04a58eb49a4a56babd3219b07f1`
- Wave: `1f64ce026f384c3baa19221930a275cf`
- Objective: Finalize the corrected multi-root workspace contract in E:\DEV\Codex-web. Primary workspace remains the control/runtime/session identity. Explicit authorized roots are valid execution scopes for agent_workflow and exec_command without switching the primary workspace. Only paths outside both primary and authorized roots fail pre-mutation with STALE_WORKSPACE_CONTEXT. Session scope remains primary-workspace-only, so authorized-root changes keep the session valid while an actual primary workspace switch invalidates a scoped stale session. Preserve unrelated changes. No restart/commit/push.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `109c2d82d04f83197647a5d1a295bcd3edbd06d8724634041a64d7674ceefb78`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19763 | 2026-08-19T05:06:32.992Z | run_started |  | PREFLIGHT |  |
| 19764 | 2026-08-19T05:06:33.461Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19765 | 2026-08-19T05:06:33.642Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19766 | 2026-08-19T05:06:33.787Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19767 | 2026-08-19T05:06:33.905Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 19768 | 2026-08-19T05:06:34.063Z | state_transition | READY | ROUTED | reason=route_selected |
| 19769 | 2026-08-19T05:06:34.516Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3fbf4cc1d9534503b3c71a08a3f20ba6 |
| 19770 | 2026-08-19T05:06:34.688Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19771 | 2026-08-19T05:06:35.165Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3fbf4cc1d9534503b3c71a08a3f20ba6 |
| 19772 | 2026-08-19T05:06:35.309Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19773 | 2026-08-19T05:06:35.670Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1ab2dfef371fbd33; input_fingerprint=4e755c9a5903eb18572b43218d0aad2028876852b25ce3aa236ebfea5573dab5 |
| 19774 | 2026-08-19T05:06:36.161Z | managed_process_admitted |  |  | owner=default |
| 19775 | 2026-08-19T05:06:36.465Z | managed_process_started |  |  | owner=default |
| 19776 | 2026-08-19T05:06:39.984Z | managed_process_terminal |  |  | owner=default |
| 19777 | 2026-08-19T05:06:40.309Z | proof_recorded |  |  | stage_id=check:1ab2dfef371fbd33; status=failed; cache_hit=False; input_fingerprint=4e755c9a5903eb18572b43218d0aad2028876852b25ce3aa236ebfea5573dab5 |
| 19778 | 2026-08-19T05:06:40.528Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 19779 | 2026-08-19T05:06:40.660Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 19780 | 2026-08-19T05:06:40.837Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 19781 | 2026-08-19T05:06:41.528Z | state_transition | REPLAN | ABORTED | reason=task_cleared |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1ab2dfef371fbd33 | failed | 4e755c9a5903eb18572b43218d0aad2028876852b25ce3aa236ebfea5573dab5 | False | 4216 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `a502992224203f66ca511e77d5bcbbbf88cbd8700cf3441521b79a057057c869`
