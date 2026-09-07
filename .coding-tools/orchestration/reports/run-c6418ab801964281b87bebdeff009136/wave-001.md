# Orchestration Wave 1

- Run: `c6418ab801964281b87bebdeff009136`
- Wave: `1587530f077948878937eef8cc1d4712`
- Objective: Read only the host/runtime lifecycle surfaces needed for the final repair. Identify: (1) where task_control restart_runtime writes its one-shot ticket and where Electron/Recovery Host consumes it; (2) the exact point after MCP termination but before replacement start where a bounded maintenance command could run; (3) existing native-LSP/WebCodex setup/binding/supervision code, if any. Return exact files/symbols and current tests. Do not modify source, Git, ledger, runtime, machine state, or services.
- Objective revision: `1`
- Objective SHA-256: `82c2cd1d14fa2b5da74793ef081158f1063255c12436e4d18111f86d7cf2e9d0`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `8e37ce49b4e1956ed036390bc8fd6202f719090e25b3a841ef4e1d71fd2ae4a4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42743 | 2026-09-07T02:36:54.825Z | run_started |  | PREFLIGHT |  |
| 42744 | 2026-09-07T02:36:55.215Z | observation_span_recorded |  |  |  |
| 42745 | 2026-09-07T02:36:55.760Z | observation_span_recorded |  |  |  |
| 42746 | 2026-09-07T02:36:55.989Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42747 | 2026-09-07T02:36:56.144Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42748 | 2026-09-07T02:36:56.359Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42749 | 2026-09-07T02:36:56.535Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42750 | 2026-09-07T02:36:56.802Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42751 | 2026-09-07T02:36:57.101Z | state_transition | READY | ROUTED | reason=route_selected |
| 42752 | 2026-09-07T02:36:57.419Z | observation_span_recorded |  |  |  |
| 42753 | 2026-09-07T02:36:58.102Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0b0c6d617506433881957f13dd5a6152 |
| 42754 | 2026-09-07T02:36:58.352Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42755 | 2026-09-07T02:36:59.332Z | observation_span_recorded |  |  |  |
| 42756 | 2026-09-07T02:36:59.827Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0b0c6d617506433881957f13dd5a6152 |
| 42757 | 2026-09-07T02:37:00.059Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42758 | 2026-09-07T02:37:00.528Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3a4713d17ffe0242; input_fingerprint=58d11a4dcaf1a9cb7f0fe177783b9c97fd358e025389067c76577ff0195c55c6 |
| 42759 | 2026-09-07T02:37:01.102Z | managed_process_admitted |  |  | owner=default |
| 42760 | 2026-09-07T02:37:01.494Z | managed_process_started |  |  | owner=default |
| 42761 | 2026-09-07T02:37:01.989Z | managed_process_terminal |  |  | owner=default |
| 42762 | 2026-09-07T02:37:02.439Z | proof_recorded |  |  | stage_id=check:3a4713d17ffe0242; status=passed; cache_hit=False; input_fingerprint=58d11a4dcaf1a9cb7f0fe177783b9c97fd358e025389067c76577ff0195c55c6 |
| 42763 | 2026-09-07T02:37:02.701Z | proof_cache_miss |  |  | reason=cold; stage_id=check:206025690a84e339; input_fingerprint=c4261a7bd95b0b1609ebd76394a2520fdd307b062c16c05800b26a3445894ef3 |
| 42764 | 2026-09-07T02:37:03.128Z | managed_process_admitted |  |  | owner=default |
| 42765 | 2026-09-07T02:37:03.436Z | managed_process_started |  |  | owner=default |
| 42766 | 2026-09-07T02:37:04.723Z | managed_process_terminal |  |  | owner=default |
| 42767 | 2026-09-07T02:37:05.158Z | proof_recorded |  |  | stage_id=check:206025690a84e339; status=passed; cache_hit=False; input_fingerprint=c4261a7bd95b0b1609ebd76394a2520fdd307b062c16c05800b26a3445894ef3 |
| 42768 | 2026-09-07T02:37:05.422Z | proof_cache_miss |  |  | reason=cold; stage_id=check:eb55f4f81af543c7; input_fingerprint=58f00b11fefc135eb9dd39874a40796fc4b25b9543bf7160619cd3d03220809d |
| 42769 | 2026-09-07T02:37:05.818Z | managed_process_admitted |  |  | owner=default |
| 42770 | 2026-09-07T02:37:06.140Z | managed_process_started |  |  | owner=default |
| 42771 | 2026-09-07T02:37:06.664Z | managed_process_terminal |  |  | owner=default |
| 42772 | 2026-09-07T02:37:07.013Z | proof_recorded |  |  | stage_id=check:eb55f4f81af543c7; status=passed; cache_hit=False; input_fingerprint=58f00b11fefc135eb9dd39874a40796fc4b25b9543bf7160619cd3d03220809d |
| 42773 | 2026-09-07T02:37:07.262Z | observation_span_recorded |  |  |  |
| 42774 | 2026-09-07T02:37:07.449Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43075 | 2026-09-07T03:29:23.702Z | quality_outcome_recorded |  |  |  |
| 43076 | 2026-09-07T03:29:24.376Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43077 | 2026-09-07T03:29:24.946Z | observation_span_recorded |  |  |  |
| 43078 | 2026-09-07T03:29:25.482Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3a4713d17ffe0242 | passed | 58d11a4dcaf1a9cb7f0fe177783b9c97fd358e025389067c76577ff0195c55c6 | False | 1504 | 0 |
| check:206025690a84e339 | passed | c4261a7bd95b0b1609ebd76394a2520fdd307b062c16c05800b26a3445894ef3 | False | 2001 | 0 |
| check:eb55f4f81af543c7 | passed | 58f00b11fefc135eb9dd39874a40796fc4b25b9543bf7160619cd3d03220809d | False | 1235 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6692c89947b74c54ad7b33f052db6f1b | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 3290a7a536244dde8122131d5e9db298a50e1ca16cbaf789eb1d03b4b468537c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `251fdae8d31284fe2fb90c587c914aa5debb3a8ffffd87b401db51bdac75167a`
