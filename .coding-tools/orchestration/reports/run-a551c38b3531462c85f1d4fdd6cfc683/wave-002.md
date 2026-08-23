# Orchestration Wave 2

- Run: `a551c38b3531462c85f1d4fdd6cfc683`
- Wave: `2c20783788f048fc88453b78988ddde8`
- Objective: Continue the same ledger maintenance safety repair after the single observed Windows durability portability failure. Change only _fsync_file so Windows uses a writable descriptor accepted by os.fsync/_commit, preserving all previously applied WAL/exclusive-gate logic and tests, then rerun the maintenance oracle.
- Objective revision: `2`
- Objective SHA-256: `60163c1c26e55c7f158aead09e2fbe33f193129e9428255145dffba8d9186e7f`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `0a9d4c1325624a85f051beabb5a9af88bae9d691`
- Worktree fingerprint: `8bba55c4f5e6d8f31d014062ad301999e560d236d1fa1aa7548c7003ceefaec4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28212 | 2026-08-23T01:57:26.630Z | wave_replanned |  | PREFLIGHT | reason=CHECK_FAILED was isolated to Windows OSError Errno 9 because _fsync_file opened the candidate with mode rb; Windows os.fsync/_commit requires a writable descriptor. This wave changes only the durability helper to os.open(..., O_RDWR) with exception-safe close and reruns the same oracle. |
| 28213 | 2026-08-23T01:57:26.781Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28214 | 2026-08-23T01:57:26.945Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28215 | 2026-08-23T01:57:27.072Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 28216 | 2026-08-23T01:57:27.240Z | state_transition | READY | ROUTED | reason=route_selected |
| 28217 | 2026-08-23T01:57:28.062Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f0cc0be89d694a0aa5b8e778048283e5 |
| 28218 | 2026-08-23T01:57:28.223Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28219 | 2026-08-23T01:57:29.003Z | patch_surface_observed |  |  |  |
| 28220 | 2026-08-23T01:57:29.302Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f0cc0be89d694a0aa5b8e778048283e5 |
| 28221 | 2026-08-23T01:57:29.440Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28222 | 2026-08-23T01:57:30.196Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b615db69c654bf6d; input_fingerprint=6ab2d0a397c3e6cac34cf594ba7532acf9a2c009b7505edcfe2dd295c3944105 |
| 28223 | 2026-08-23T01:57:30.505Z | managed_process_admitted |  |  | owner=default |
| 28224 | 2026-08-23T01:57:30.814Z | managed_process_started |  |  | owner=default |
| 28225 | 2026-08-23T01:57:31.239Z | managed_process_terminal |  |  | owner=default |
| 28226 | 2026-08-23T01:57:31.538Z | proof_recorded |  |  | stage_id=check:b615db69c654bf6d; status=passed; cache_hit=False; input_fingerprint=6ab2d0a397c3e6cac34cf594ba7532acf9a2c009b7505edcfe2dd295c3944105 |
| 28227 | 2026-08-23T01:57:31.769Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f4400f0114f4b155; input_fingerprint=0460231e7dfbaa1c69bd9e2e93cde86213d0d92613e22e1b9bb73368e75db234 |
| 28228 | 2026-08-23T01:57:32.106Z | managed_process_admitted |  |  | owner=default |
| 28229 | 2026-08-23T01:57:32.398Z | managed_process_started |  |  | owner=default |
| 28230 | 2026-08-23T01:57:34.570Z | managed_process_terminal |  |  | owner=default |
| 28231 | 2026-08-23T01:57:34.909Z | proof_recorded |  |  | stage_id=check:f4400f0114f4b155; status=passed; cache_hit=False; input_fingerprint=0460231e7dfbaa1c69bd9e2e93cde86213d0d92613e22e1b9bb73368e75db234 |
| 28232 | 2026-08-23T01:57:35.091Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=45391813cdbcfbedfe25dffa250b8636d89227c4da15aa8932f3ca24ade579bd |
| 28233 | 2026-08-23T01:57:35.410Z | managed_process_admitted |  |  | owner=default |
| 28234 | 2026-08-23T01:57:35.739Z | managed_process_started |  |  | owner=default |
| 28235 | 2026-08-23T01:57:37.880Z | managed_process_terminal |  |  | owner=default |
| 28236 | 2026-08-23T01:57:38.989Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=45391813cdbcfbedfe25dffa250b8636d89227c4da15aa8932f3ca24ade579bd |
| 28237 | 2026-08-23T01:57:40.003Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 28238 | 2026-08-23T02:51:17.962Z | quality_outcome_recorded |  |  |  |
| 28239 | 2026-08-23T02:51:18.124Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 28240 | 2026-08-23T02:51:18.439Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b615db69c654bf6d | passed | 6ab2d0a397c3e6cac34cf594ba7532acf9a2c009b7505edcfe2dd295c3944105 | False | 1037 | 0 |
| check:f4400f0114f4b155 | passed | 0460231e7dfbaa1c69bd9e2e93cde86213d0d92613e22e1b9bb73368e75db234 | False | 2806 | 0 |
| verify:tests | passed | 45391813cdbcfbedfe25dffa250b8636d89227c4da15aa8932f3ca24ade579bd | False | 3562 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 9521a50d805245d984e48c4c8b022f11 | accepted | 0a9d4c1325624a85f051beabb5a9af88bae9d691 | 20f1d14faacf4e36e05236b0cb13ba1c5d984aa7892eeda3cabf8a2a810dfb31 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `53`
- Chain head: `fbb3b6dbcb8fbd35a5ac70962e1491b5346b7ddbe2c29c9a8a113bab30e9c61b`
