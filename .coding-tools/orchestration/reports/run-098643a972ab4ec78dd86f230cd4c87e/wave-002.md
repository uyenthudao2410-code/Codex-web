# Orchestration Wave 2

- Run: `098643a972ab4ec78dd86f230cd4c87e`
- Wave: `3a35436bd9614500a7c890138902abc3`
- Objective: Diagnose the live Recovery Tunnel failure shown by the operator after configuring a distinct recoveryTunnelId. Read-only investigation only. Identify whether the failure is caused by tunnel ID/account provisioning, Runtime API Key/auth, proxy/network, tunnel-client invocation, process lifecycle, or missing recovery-specific configuration. Preserve fail-closed behavior and do not mutate source/config/runtime yet. Return the exact local evidence paths/status fields and the smallest next proof needed.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `4aa98c721f9ba147fa726e2c67bc3a0f2762dee60d56d5a2be5b1cb5b14b0322`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 7056 | 2026-08-16T10:35:56.064Z | wave_replanned |  | PREFLIGHT | reason=Live recovery-tunnel.log proved the shipped tunnel-client rejects channel=recovery before any network/auth attempt because every tunnel instance requires a channel=main. Additional local CLI proof showed tunnel-client health --require-control-plane-poll is the authoritative remote-readiness oracle, and the 5s Recovery Host supervision interval can overlap the prior 15s recovery-tunnel readiness loop on failures. |
| 7057 | 2026-08-16T10:35:56.148Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 7058 | 2026-08-16T10:35:56.261Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 7059 | 2026-08-16T10:35:56.372Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 7060 | 2026-08-16T10:35:56.486Z | state_transition | READY | ROUTED | reason=route_selected |
| 7061 | 2026-08-16T10:35:56.874Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f39277ceee1b496da39f1d358c682a7e |
| 7062 | 2026-08-16T10:35:56.975Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 7063 | 2026-08-16T10:35:57.391Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f39277ceee1b496da39f1d358c682a7e |
| 7064 | 2026-08-16T10:35:57.501Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 7065 | 2026-08-16T10:35:57.804Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8d444d33922441a9; input_fingerprint=eb88a4f9e5e77b050b546a681f03381a5d8303e0743a337405d1eda0634d519c |
| 7066 | 2026-08-16T10:35:58.025Z | managed_process_admitted |  |  | owner=default |
| 7067 | 2026-08-16T10:35:58.232Z | managed_process_started |  |  | owner=default |
| 7068 | 2026-08-16T10:35:59.380Z | managed_process_terminal |  |  | owner=default |
| 7069 | 2026-08-16T10:35:59.677Z | proof_recorded |  |  | stage_id=check:8d444d33922441a9; status=passed; cache_hit=False; input_fingerprint=eb88a4f9e5e77b050b546a681f03381a5d8303e0743a337405d1eda0634d519c |
| 7070 | 2026-08-16T10:35:59.805Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4e484c871a44ba1c; input_fingerprint=147a8f6c702434aa1f44abb2955e06618edfe69fd5bd903e50fdb89dfdb5b368 |
| 7071 | 2026-08-16T10:36:00.047Z | managed_process_admitted |  |  | owner=default |
| 7072 | 2026-08-16T10:36:00.249Z | managed_process_started |  |  | owner=default |
| 7073 | 2026-08-16T10:36:00.565Z | managed_process_terminal |  |  | owner=default |
| 7074 | 2026-08-16T10:36:00.977Z | proof_recorded |  |  | stage_id=check:4e484c871a44ba1c; status=passed; cache_hit=False; input_fingerprint=147a8f6c702434aa1f44abb2955e06618edfe69fd5bd903e50fdb89dfdb5b368 |
| 7075 | 2026-08-16T10:36:01.104Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c78f4d08899ed1d42a38b782678c7bc60ccee12c82c126582d01dd72b8bc4b1d |
| 7076 | 2026-08-16T10:36:01.399Z | managed_process_admitted |  |  | owner=default |
| 7077 | 2026-08-16T10:36:01.616Z | managed_process_started |  |  | owner=default |
| 7078 | 2026-08-16T10:36:24.537Z | managed_process_terminal |  |  | owner=default |
| 7079 | 2026-08-16T10:36:24.791Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c78f4d08899ed1d42a38b782678c7bc60ccee12c82c126582d01dd72b8bc4b1d |
| 7080 | 2026-08-16T10:36:25.216Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 7081 | 2026-08-16T10:36:36.179Z | managed_process_admitted |  |  | owner=default |
| 7082 | 2026-08-16T10:36:36.513Z | managed_process_started |  |  | owner=default |
| 7083 | 2026-08-16T10:36:36.891Z | managed_process_terminal |  |  | owner=default |
| 7084 | 2026-08-16T10:36:44.287Z | managed_process_admitted |  |  | owner=default |
| 7085 | 2026-08-16T10:36:44.482Z | managed_process_started |  |  | owner=default |
| 7086 | 2026-08-16T10:36:44.788Z | managed_process_terminal |  |  | owner=default |
| 7087 | 2026-08-16T10:36:51.690Z | managed_process_admitted |  |  | owner=default |
| 7088 | 2026-08-16T10:36:51.887Z | managed_process_started |  |  | owner=default |
| 7089 | 2026-08-16T10:36:52.358Z | managed_process_terminal |  |  | owner=default |
| 7090 | 2026-08-16T10:36:58.748Z | managed_process_admitted |  |  | owner=default |
| 7091 | 2026-08-16T10:36:58.945Z | managed_process_started |  |  | owner=default |
| 7092 | 2026-08-16T10:36:59.262Z | managed_process_terminal |  |  | owner=default |
| 7093 | 2026-08-16T10:37:04.196Z | managed_process_admitted |  |  | owner=default |
| 7094 | 2026-08-16T10:37:04.421Z | managed_process_started |  |  | owner=default |
| 7095 | 2026-08-16T10:37:04.921Z | managed_process_terminal |  |  | owner=default |
| 7096 | 2026-08-16T10:37:12.139Z | managed_process_admitted |  |  | owner=default |
| 7097 | 2026-08-16T10:37:12.379Z | managed_process_started |  |  | owner=default |
| 7098 | 2026-08-16T10:37:12.865Z | managed_process_terminal |  |  | owner=default |
| 7099 | 2026-08-16T10:37:19.101Z | managed_process_admitted |  |  | owner=default |
| 7100 | 2026-08-16T10:37:19.345Z | managed_process_started |  |  | owner=default |
| 7101 | 2026-08-16T10:37:19.672Z | managed_process_terminal |  |  | owner=default |
| 7102 | 2026-08-16T10:37:24.631Z | managed_process_admitted |  |  | owner=default |
| 7103 | 2026-08-16T10:37:24.854Z | managed_process_started |  |  | owner=default |
| 7104 | 2026-08-16T10:37:25.738Z | managed_process_terminal |  |  | owner=default |
| 7105 | 2026-08-16T10:37:37.298Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 7106 | 2026-08-16T10:37:37.539Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8d444d33922441a9 | passed | eb88a4f9e5e77b050b546a681f03381a5d8303e0743a337405d1eda0634d519c | False | 1609 | 0 |
| check:4e484c871a44ba1c | passed | 147a8f6c702434aa1f44abb2955e06618edfe69fd5bd903e50fdb89dfdb5b368 | False | 874 | 0 |
| verify:tests | passed | c78f4d08899ed1d42a38b782678c7bc60ccee12c82c126582d01dd72b8bc4b1d | False | 23405 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 540226ccd1b04aecab833747344f2529 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 44acfac8e19c658314be22e18aa5320002218aafb0aa8f455fd2dc02bfce620b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `80`
- Chain head: `179eb5ad157300a163b96251ed6b63fb344a06959da2eb0b963c551d64b03e42`
