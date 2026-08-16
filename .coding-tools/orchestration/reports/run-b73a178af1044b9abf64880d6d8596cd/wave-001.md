# Orchestration Wave 1

- Run: `b73a178af1044b9abf64880d6d8596cd`
- Wave: `60c0d142771d4b73a9d8e000a9c0c21a`
- Objective: Diagnose remaining Phase 3 runtime blockers after the accepted per-component baseline-head fix. External Recovery Supervisor was installed and previously passed a real kill/revive canary, but its recorded PID 16656 is now dead and Scheduled Task reports Ready with last check around 09:21Z. Current Recovery Host PID 5504 started later at 09:36Z and spawned fresh primary MCP/Tunnel PIDs 7932/9052. recovery-plane-state.json exists but the current read showed no live Recovery MCP/Tunnel fields. Determine from source and tests: (1) why recovery-supervisor.ps1 exits instead of remaining a durable same-user resurrection loop, including scheduled-task settings/loop termination/error paths; (2) whether RecoveryHost actually starts RecoveryPlaneService and what recovery-plane-state schema/process adoption should look like; (3) the smallest safe changes and exact real-process acceptance proof to make supervisor remain live, Recovery MCP independent and running, Recovery Tunnel fail-closed when no second tunnel ID, and primary MCP/Tunnel untouched during Recovery Host resurrection. Preserve current dirty Phase 3 source and unrelated WIP.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `fab5f3a75a62f57ee9ebbf0885ddf767f437cd153972e1e61b04dda363e851d8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6830 | 2026-08-16T09:46:45.581Z | run_started |  | PREFLIGHT |  |
| 6831 | 2026-08-16T09:46:48.600Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6832 | 2026-08-16T09:47:47.508Z | managed_process_admitted |  |  | owner=default |
| 6833 | 2026-08-16T09:47:47.714Z | managed_process_started |  |  | owner=default |
| 6834 | 2026-08-16T09:47:49.155Z | managed_process_terminal |  |  | owner=default |
| 6835 | 2026-08-16T09:48:05.135Z | managed_process_admitted |  |  | owner=default |
| 6836 | 2026-08-16T09:48:05.339Z | managed_process_started |  |  | owner=default |
| 6837 | 2026-08-16T09:48:06.809Z | managed_process_terminal |  |  | owner=default |
| 6838 | 2026-08-16T09:49:01.534Z | managed_process_admitted |  |  | owner=default |
| 6839 | 2026-08-16T09:49:01.748Z | managed_process_started |  |  | owner=default |
| 6840 | 2026-08-16T09:49:02.123Z | managed_process_terminal |  |  | owner=default |
| 6841 | 2026-08-16T09:49:10.037Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6842 | 2026-08-16T09:49:36.026Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6843 | 2026-08-16T09:49:36.175Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6844 | 2026-08-16T09:49:36.299Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6845 | 2026-08-16T09:49:36.427Z | state_transition | READY | ROUTED | reason=route_selected |
| 6846 | 2026-08-16T09:49:36.824Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=88b0612ddb664dabaa0544c1b7910431 |
| 6847 | 2026-08-16T09:49:36.915Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6848 | 2026-08-16T09:49:37.356Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=88b0612ddb664dabaa0544c1b7910431 |
| 6849 | 2026-08-16T09:49:37.457Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6850 | 2026-08-16T09:49:37.770Z | proof_cache_miss |  |  | reason=cold; stage_id=check:96cf305ed909862a; input_fingerprint=d0ec6b314d979dcde61a561ecfc160fbcb9dd2045773e221850a0324de08479c |
| 6851 | 2026-08-16T09:49:38.023Z | managed_process_admitted |  |  | owner=default |
| 6852 | 2026-08-16T09:49:38.252Z | managed_process_started |  |  | owner=default |
| 6853 | 2026-08-16T09:49:38.675Z | managed_process_terminal |  |  | owner=default |
| 6854 | 2026-08-16T09:49:38.896Z | proof_recorded |  |  | stage_id=check:96cf305ed909862a; status=passed; cache_hit=False; input_fingerprint=d0ec6b314d979dcde61a561ecfc160fbcb9dd2045773e221850a0324de08479c |
| 6855 | 2026-08-16T09:49:39.014Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=87395c9894a4497809786e6938c1bb8b4e36503626223fcb2c01472f8123fcf3 |
| 6856 | 2026-08-16T09:49:39.238Z | managed_process_admitted |  |  | owner=default |
| 6857 | 2026-08-16T09:49:39.468Z | managed_process_started |  |  | owner=default |
| 6858 | 2026-08-16T09:49:47.408Z | managed_process_terminal |  |  | owner=default |
| 6859 | 2026-08-16T09:49:47.648Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=87395c9894a4497809786e6938c1bb8b4e36503626223fcb2c01472f8123fcf3 |
| 6860 | 2026-08-16T09:49:47.759Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ad2d5daf5ea84686d48392ef3c7abadbec959385d0e8da68c499d2a9e0cfd106 |
| 6861 | 2026-08-16T09:49:47.989Z | managed_process_admitted |  |  | owner=default |
| 6862 | 2026-08-16T09:49:48.198Z | managed_process_started |  |  | owner=default |
| 6863 | 2026-08-16T09:50:05.043Z | managed_process_terminal |  |  | owner=default |
| 6864 | 2026-08-16T09:50:05.389Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ad2d5daf5ea84686d48392ef3c7abadbec959385d0e8da68c499d2a9e0cfd106 |
| 6865 | 2026-08-16T09:50:05.855Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6866 | 2026-08-16T09:50:33.469Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6867 | 2026-08-16T09:50:33.744Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:96cf305ed909862a | passed | d0ec6b314d979dcde61a561ecfc160fbcb9dd2045773e221850a0324de08479c | False | 926 | 0 |
| check:fe3ffbf7aa7a92a6 | passed | 87395c9894a4497809786e6938c1bb8b4e36503626223fcb2c01472f8123fcf3 | False | 8418 | 0 |
| verify:tests | passed | ad2d5daf5ea84686d48392ef3c7abadbec959385d0e8da68c499d2a9e0cfd106 | False | 17297 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 96be4241d5b441258f4ce245d652c65a | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 873d0d1c6dc21cf06e449a4818b2aa2e399211d6c0af29baf0782dc74b3bb359 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `07511abd87000ac0881583481a3d433bdcda88ee89d356a0dabf5c1364968be5`
