# Orchestration Wave 1

- Run: `d38ed4a4167e4121a3b44f505877aae5`
- Wave: `0548a9073c4a4ab692d47540297433df`
- Objective: RUN-MW-CLOSURE: verify exact multi-workspace isolation, durable context, and scoped control on the current Codex-web worktree.
- Objective revision: `1`
- Objective SHA-256: `c02cf4099441e84652f1280ecb069139a8a13c75c9dd1dd6c67ad1cbb7915a89`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `4d77edd521658d14d6f5125b1e8ff3498e80a77f`
- Worktree fingerprint: `1e10aafa8d2dbcb94016d25007b474c49c11cb2e4d2a78a0094330dc48477c52`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28855 | 2026-08-24T11:54:13.252Z | run_started |  | PREFLIGHT |  |
| 28856 | 2026-08-24T11:54:13.634Z | observation_span_recorded |  |  |  |
| 28857 | 2026-08-24T11:54:13.873Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28858 | 2026-08-24T11:54:14.033Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28859 | 2026-08-24T11:54:14.219Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28860 | 2026-08-24T11:54:14.360Z | state_transition | READY | ROUTED | reason=route_selected |
| 28861 | 2026-08-24T11:54:14.622Z | observation_span_recorded |  |  |  |
| 28862 | 2026-08-24T11:54:16.346Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=29a3d823a82e4575bba24a4366cd1a84 |
| 28863 | 2026-08-24T11:54:16.532Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28864 | 2026-08-24T11:54:17.868Z | observation_span_recorded |  |  |  |
| 28865 | 2026-08-24T11:54:18.136Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=29a3d823a82e4575bba24a4366cd1a84 |
| 28866 | 2026-08-24T11:54:18.294Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28867 | 2026-08-24T11:54:19.532Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a5804220fb15a344; input_fingerprint=752e8164ff076edb675e2c0f3bf54593394de939937f8c58ab77b43b6e22f05d |
| 28868 | 2026-08-24T11:54:19.961Z | managed_process_admitted |  |  | owner=default |
| 28869 | 2026-08-24T11:54:20.280Z | managed_process_started |  |  | owner=default |
| 28870 | 2026-08-24T11:55:01.164Z | managed_process_terminal |  |  | owner=default |
| 28871 | 2026-08-24T11:55:01.566Z | proof_recorded |  |  | stage_id=check:a5804220fb15a344; status=passed; cache_hit=False; input_fingerprint=752e8164ff076edb675e2c0f3bf54593394de939937f8c58ab77b43b6e22f05d |
| 28872 | 2026-08-24T11:55:01.761Z | observation_span_recorded |  |  |  |
| 28873 | 2026-08-24T11:55:01.956Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 28874 | 2026-08-24T11:59:40.112Z | observation_span_recorded |  |  |  |
| 28875 | 2026-08-24T11:59:40.267Z | failure_observed | ACCEPTING | ACCEPTING | reason=Live handoff capsule lacks the required base_head/worktree_fp/write-lease provenance because the stateless task context is not propagated into the background agent_workflow thread. Replan after the scoped-context propagation fix and focused regression.; failure_class=SOL_REJECTED |
| 28876 | 2026-08-24T11:59:40.413Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 28877 | 2026-08-24T11:59:40.577Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 28878 | 2026-08-24T12:03:56.540Z | state_transition | REPLAN | ABORTED | reason=task_stopped |
| 28879 | 2026-08-24T12:03:56.941Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a5804220fb15a344 | passed | 752e8164ff076edb675e2c0f3bf54593394de939937f8c58ab77b43b6e22f05d | False | 41680 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `f67dbf70ff68a15157f07daa37c9f814c3cab3c76e8c067cd3d972743a8818a0`
