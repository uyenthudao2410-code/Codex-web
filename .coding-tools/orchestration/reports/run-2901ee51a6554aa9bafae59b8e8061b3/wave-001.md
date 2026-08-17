# Orchestration Wave 1

- Run: `2901ee51a6554aa9bafae59b8e8061b3`
- Wave: `3f93de86d6654f1bb353e143eed1fc57`
- Objective: Fix the remaining live Recovery Tunnel OWNER_UNVERIFIED failure after successful Recovery Host/UI activation. Live runtime state proves all recoveryTunnel PID/owner/fingerprint fields are null while RecoveryPlaneService reports RECOVERY_TUNNEL_OWNER_UNVERIFIED. Inspect every RecoveryPlaneService liveness guard that coerces stored nullable PID fields with Number(...) before isAlive, especially normal ensure/start paths for recovery tunnel/MCP/candidate. Identify all same-class null->0 guards and the smallest coherent fix so absent PID state means 'not running', while positive real PIDs retain existing fail-closed ownership behavior. Preserve unrelated WIP.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `db44e216e12ccf3a6362e8f7cfa578d06b52456660aba04ffb367564a77da6ed`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11826 | 2026-08-17T06:52:40.868Z | run_started |  | PREFLIGHT |  |
| 11827 | 2026-08-17T06:52:45.865Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11828 | 2026-08-17T06:54:15.086Z | managed_process_admitted |  |  | owner=chatweb |
| 11829 | 2026-08-17T06:54:15.408Z | managed_process_started |  |  | owner=chatweb |
| 11830 | 2026-08-17T06:54:17.277Z | managed_process_terminal |  |  | owner=chatweb |
| 11831 | 2026-08-17T06:55:09.812Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11832 | 2026-08-17T06:55:09.952Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11833 | 2026-08-17T06:55:10.135Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11834 | 2026-08-17T06:55:10.365Z | state_transition | READY | ROUTED | reason=route_selected |
| 11835 | 2026-08-17T06:55:10.889Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=62161adb56314a6caafe59ab7216cc48 |
| 11836 | 2026-08-17T06:55:11.063Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11837 | 2026-08-17T06:55:11.856Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=62161adb56314a6caafe59ab7216cc48 |
| 11838 | 2026-08-17T06:55:12.072Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11839 | 2026-08-17T06:55:12.615Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a93edb4da0e64a89; input_fingerprint=63bd1d7cd1f27ba6c5c98bd95c4d8a6bdce64fb0d34b7e7582eb97791f5ff3d1 |
| 11840 | 2026-08-17T06:55:13.178Z | managed_process_admitted |  |  | owner=default |
| 11841 | 2026-08-17T06:55:13.528Z | managed_process_started |  |  | owner=default |
| 11842 | 2026-08-17T06:55:14.045Z | managed_process_terminal |  |  | owner=default |
| 11843 | 2026-08-17T06:55:14.412Z | proof_recorded |  |  | stage_id=check:a93edb4da0e64a89; status=passed; cache_hit=False; input_fingerprint=63bd1d7cd1f27ba6c5c98bd95c4d8a6bdce64fb0d34b7e7582eb97791f5ff3d1 |
| 11844 | 2026-08-17T06:55:14.636Z | proof_cache_miss |  |  | reason=cold; stage_id=check:639bdd33a5b3aa44; input_fingerprint=eda041f59c7b76a7993d2b812cef040775acfad4e16486194c7b3a40e201aa11 |
| 11845 | 2026-08-17T06:55:14.995Z | managed_process_admitted |  |  | owner=default |
| 11846 | 2026-08-17T06:55:15.328Z | managed_process_started |  |  | owner=default |
| 11847 | 2026-08-17T06:55:15.803Z | managed_process_terminal |  |  | owner=default |
| 11848 | 2026-08-17T06:55:16.218Z | proof_recorded |  |  | stage_id=check:639bdd33a5b3aa44; status=passed; cache_hit=False; input_fingerprint=eda041f59c7b76a7993d2b812cef040775acfad4e16486194c7b3a40e201aa11 |
| 11849 | 2026-08-17T06:55:16.385Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:b39a03c60a5b0526; input_fingerprint=a14f867a07a5f27dbcbb3953506cad5a292d83e5a99cee7fb5a7c468cf8947c5 |
| 11850 | 2026-08-17T06:55:16.800Z | managed_process_admitted |  |  | owner=default |
| 11851 | 2026-08-17T06:55:17.113Z | managed_process_started |  |  | owner=default |
| 11852 | 2026-08-17T06:55:17.613Z | managed_process_terminal |  |  | owner=default |
| 11853 | 2026-08-17T06:55:17.971Z | proof_recorded |  |  | stage_id=check:b39a03c60a5b0526; status=passed; cache_hit=False; input_fingerprint=a14f867a07a5f27dbcbb3953506cad5a292d83e5a99cee7fb5a7c468cf8947c5 |
| 11854 | 2026-08-17T06:55:18.250Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9f3f83d6b46d2388; input_fingerprint=8f9ede1f1f9b6d7cb8e94c82e9d1aae97c44ef42337d291308da7ad9a48fbb92 |
| 11855 | 2026-08-17T06:55:18.751Z | managed_process_admitted |  |  | owner=default |
| 11856 | 2026-08-17T06:55:19.092Z | managed_process_started |  |  | owner=default |
| 11857 | 2026-08-17T06:55:19.755Z | managed_process_admitted |  |  | owner=chatweb |
| 11858 | 2026-08-17T06:55:20.075Z | managed_process_terminal |  |  | owner=default |
| 11859 | 2026-08-17T06:55:20.196Z | managed_process_started |  |  | owner=chatweb |
| 11860 | 2026-08-17T06:55:20.714Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=8f9ede1f1f9b6d7cb8e94c82e9d1aae97c44ef42337d291308da7ad9a48fbb92 |
| 11861 | 2026-08-17T06:55:21.655Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11862 | 2026-08-17T06:55:28.803Z | managed_process_terminal |  |  | owner=chatweb |
| 11863 | 2026-08-17T06:55:58.517Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11864 | 2026-08-17T06:55:58.909Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a93edb4da0e64a89 | passed | 63bd1d7cd1f27ba6c5c98bd95c4d8a6bdce64fb0d34b7e7582eb97791f5ff3d1 | False | 1361 | 0 |
| check:639bdd33a5b3aa44 | passed | eda041f59c7b76a7993d2b812cef040775acfad4e16486194c7b3a40e201aa11 | False | 1202 | 0 |
| check:b39a03c60a5b0526 | passed | a14f867a07a5f27dbcbb3953506cad5a292d83e5a99cee7fb5a7c468cf8947c5 | False | 1225 | 0 |
| check:9f3f83d6b46d2388 | passed | 8f9ede1f1f9b6d7cb8e94c82e9d1aae97c44ef42337d291308da7ad9a48fbb92 | False | 1853 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5aaebcdf3bd04ecab860e9a0ec96e963 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | c8206fa943d94e206b3682606a77091cb3e1dca1e77ff6d557111c3629e156ee | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `39`
- Chain head: `42c316c78da32c49d05cc6bb59c6fde6f5e88302efdcc148f172241a22855677`
