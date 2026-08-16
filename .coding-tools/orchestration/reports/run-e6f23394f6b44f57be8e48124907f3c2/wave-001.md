# Orchestration Wave 1

- Run: `e6f23394f6b44f57be8e48124907f3c2`
- Wave: `bfeda33d50ab44f9811197ae6377b037`
- Objective: Fix the live Windows Recovery Host handoff continuity defect proven by the accepted-code canary: after Recovery Host replacement completed, both Coding MCP and Tunnel processes were recreated ~16 seconds later because their child spawns were attached to the exiting Recovery Host lifetime. Make NativeService and TunnelService child processes detached from the Recovery Host while keeping windowsHide, file-backed stdio, unref, explicit PID state, and existing taskkill /T /F stop ownership. Update the lifecycle regression that previously asserted detached:false to require detached:true and document the handoff continuity invariant. Modify only electron/services/nativeService.js, electron/services/tunnelService.js, and tests/runtime-lifecycle.test.js. Preserve all unrelated dirty work.
- Mode: `mcp_only`
- Base HEAD: `597170860118a847b7e8a6f06903c37da8432d82`
- Worktree fingerprint: `a37b6c7a7d5deff119b190fa9ecf5a1c34c5442e8b4926dfa92a3e59a12870d5`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6121 | 2026-08-16T06:46:37.176Z | run_started |  | PREFLIGHT |  |
| 6122 | 2026-08-16T06:46:37.521Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6123 | 2026-08-16T06:46:37.657Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6124 | 2026-08-16T06:46:37.788Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6125 | 2026-08-16T06:46:37.926Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6126 | 2026-08-16T06:46:38.026Z | state_transition | READY | ROUTED | reason=route_selected |
| 6127 | 2026-08-16T06:46:38.406Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6246de70aa624909a78986ca79ec97c8 |
| 6128 | 2026-08-16T06:46:38.536Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6129 | 2026-08-16T06:46:38.993Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6246de70aa624909a78986ca79ec97c8 |
| 6130 | 2026-08-16T06:46:39.139Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6131 | 2026-08-16T06:46:39.442Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=25118a6bd2a7a4506991624f3e2c71830eb656a84b7d52ca3c3febc3c9cbda5d |
| 6132 | 2026-08-16T06:46:39.733Z | managed_process_admitted |  |  | owner=default |
| 6133 | 2026-08-16T06:46:39.965Z | managed_process_started |  |  | owner=default |
| 6134 | 2026-08-16T06:46:40.387Z | managed_process_terminal |  |  | owner=default |
| 6135 | 2026-08-16T06:46:40.636Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=25118a6bd2a7a4506991624f3e2c71830eb656a84b7d52ca3c3febc3c9cbda5d |
| 6136 | 2026-08-16T06:46:41.103Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6137 | 2026-08-16T06:47:28.937Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6138 | 2026-08-16T06:47:29.186Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 25118a6bd2a7a4506991624f3e2c71830eb656a84b7d52ca3c3febc3c9cbda5d | False | 937 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| fc2f47aafe34446c97d0c7509ce3f914 | accepted | 597170860118a847b7e8a6f06903c37da8432d82 | cba61638be9413414b9f5d09bead42ab3226edca883485f844b7255759e95c6a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `1d6091723948493beb970e877de77eca340e7550b20c0b5c8dda0c040e29dcce`
