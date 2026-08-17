# Orchestration Wave 2

- Run: `f6c9de68597b442fa51c570ec712dba9`
- Wave: `d69559cfe6244c4ba3238d68f91081e3`
- Objective: READ ONLY. Diagnose the Coding MCP connection/runtime routing architecture responsible for one ChatGPT plugin session landing workspace_context on E:\DEV\Tools-Codex-web while exec_command/agent_workflow land E:\Github\Tools-Codex-web. Do not mutate. Localize HTTP session creation, runtime selection, workspace switching, hub client identity, Electron supervisor registration/health/restart, and any stale endpoint/fallback behavior. Recommend the smallest fail-closed session-affinity fix with exact files/symbols and focused tests.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `5395add0b06708b11ba2c8cdcbe16ef632957f5f6874a63edbd4d6870e2c501c`
- Contract fingerprint: `a6dfcf969cdf4199046f63b936c6d719e7fc89cdc21389ae947755fa2645420e`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11080 | 2026-08-17T03:35:44.572Z | wave_replanned |  | PREFLIGHT | reason=The previous wave targeted a local workspace-affinity/tunnel symptom. The user clarified the root requirement is a true multi-device identity/routing/project/lease architecture. Replace the symptom-fix strategy with M1-M4 design and implementation while preserving DEV as authoritative workspace and all unrelated WIP. |
| 11081 | 2026-08-17T03:35:45.342Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11082 | 2026-08-17T03:36:21.956Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11083 | 2026-08-17T03:37:59.686Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11084 | 2026-08-17T03:38:17.362Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11085 | 2026-08-17T03:39:35.255Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11086 | 2026-08-17T03:39:52.635Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11087 | 2026-08-17T03:41:00.371Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11088 | 2026-08-17T03:41:19.389Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11089 | 2026-08-17T03:42:36.231Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11090 | 2026-08-17T03:42:57.953Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11091 | 2026-08-17T03:44:13.852Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11092 | 2026-08-17T03:44:35.002Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11093 | 2026-08-17T03:45:43.317Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11094 | 2026-08-17T03:46:19.640Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11095 | 2026-08-17T03:46:19.827Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11096 | 2026-08-17T03:46:20.019Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11097 | 2026-08-17T03:46:20.211Z | state_transition | READY | ROUTED | reason=route_selected |
| 11098 | 2026-08-17T03:46:20.677Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=34bdb1c8f68a419fbbd1beccf43fd5ba |
| 11099 | 2026-08-17T03:46:20.827Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11100 | 2026-08-17T03:46:21.437Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=34bdb1c8f68a419fbbd1beccf43fd5ba |
| 11101 | 2026-08-17T03:46:21.576Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11102 | 2026-08-17T03:46:22.091Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7fed0f5a14066191; input_fingerprint=8387a0e165d8ee271b1963aa8f32d731055e84b643fa9f23bdf929d03d52db9e |
| 11103 | 2026-08-17T03:46:22.400Z | managed_process_admitted |  |  | owner=default |
| 11104 | 2026-08-17T03:46:22.678Z | managed_process_started |  |  | owner=default |
| 11105 | 2026-08-17T03:46:23.226Z | managed_process_terminal |  |  | owner=default |
| 11106 | 2026-08-17T03:46:23.578Z | proof_recorded |  |  | stage_id=check:7fed0f5a14066191; status=passed; cache_hit=False; input_fingerprint=8387a0e165d8ee271b1963aa8f32d731055e84b643fa9f23bdf929d03d52db9e |
| 11107 | 2026-08-17T03:46:23.746Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3856d101215629ca46ddef817681d34182981f0f4d0a08f0fe94651c25d9766d |
| 11108 | 2026-08-17T03:46:24.143Z | managed_process_admitted |  |  | owner=default |
| 11109 | 2026-08-17T03:46:24.532Z | managed_process_started |  |  | owner=default |
| 11110 | 2026-08-17T03:46:25.614Z | managed_process_terminal |  |  | owner=default |
| 11111 | 2026-08-17T03:46:27.063Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3856d101215629ca46ddef817681d34182981f0f4d0a08f0fe94651c25d9766d |
| 11112 | 2026-08-17T03:46:27.680Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11113 | 2026-08-17T03:49:42.316Z | managed_process_admitted |  |  | owner=default |
| 11114 | 2026-08-17T03:49:42.613Z | managed_process_started |  |  | owner=default |
| 11115 | 2026-08-17T03:49:44.005Z | managed_process_terminal |  |  | owner=default |
| 11116 | 2026-08-17T03:50:01.097Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11117 | 2026-08-17T03:50:01.517Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7fed0f5a14066191 | passed | 8387a0e165d8ee271b1963aa8f32d731055e84b643fa9f23bdf929d03d52db9e | False | 1143 | 0 |
| verify:tests | passed | 3856d101215629ca46ddef817681d34182981f0f4d0a08f0fe94651c25d9766d | False | 2828 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 842a487f86504880b2620e78ae920fdd | accepted | 3a3abaff72a8e6382e4c362865becba069e4ecfc | 378aade8e4cf123b3b2dda195605895a381445a3a9503e3eda2eade580fec036 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `58`
- Chain head: `fdfe464941c3fc0c9026005fd8647c435a1d4aac3b3b933cab9d7887ae7d9332`
