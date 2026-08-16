# Orchestration Wave 2

- Run: `d9c08fc64fe34d17ad13915bfc8cc778`
- Wave: `0466900a5f9940d591518328c057d519`
- Objective: Resume and complete the accepted-code automatic activation work after the MCP reconnect. Inspect the already-present Recovery Host auto-activation controller and related wiring, then prepare the minimal integration delta that changes trust from a single-wave modified_files gate to a running-baseline plus canonical accepted SHA-256 receipt union. Preserve unrelated dirty Python/Rust/docs/.coding-tools work. Future activation must remain Recovery Host-owned, fail closed on unaccepted byte drift, avoid source watchers/restart-all/arbitrary paths, and use existing Safe Code Activation component order. Do not mutate in this prepare phase.
- Mode: `mcp_only`
- Base HEAD: `597170860118a847b7e8a6f06903c37da8432d82`
- Worktree fingerprint: `967d297a5a1dd00de9deaa31a2fdc18eaafefccb21f133c4d65875a411963688`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6039 | 2026-08-16T06:12:15.679Z | wave_replanned |  | PREFLIGHT | reason=The source-only wave parsed, but the old tests intentionally lacked accepted_files receipts and therefore correctly failed under the new fail-closed trust contract. The evidence strategy changes to canonical receipt fixtures plus explicit running/disk revision oracles, while keeping the already-applied V2 source. |
| 6040 | 2026-08-16T06:12:15.830Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6041 | 2026-08-16T06:12:15.960Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6042 | 2026-08-16T06:12:16.109Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6043 | 2026-08-16T06:12:16.260Z | state_transition | READY | ROUTED | reason=route_selected |
| 6044 | 2026-08-16T06:12:16.730Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=77e1b003b894443f81cf6846f599a627 |
| 6045 | 2026-08-16T06:12:16.893Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6046 | 2026-08-16T06:12:17.391Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=77e1b003b894443f81cf6846f599a627 |
| 6047 | 2026-08-16T06:12:17.509Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6048 | 2026-08-16T06:12:17.852Z | proof_cache_miss |  |  | reason=cold; stage_id=check:16333285e684aa5c; input_fingerprint=07ae1c3ee8bbaafa525b11abf1043fbd681b81feb01789484390cf52b64d31d6 |
| 6049 | 2026-08-16T06:12:18.127Z | managed_process_admitted |  |  | owner=default |
| 6050 | 2026-08-16T06:12:18.372Z | managed_process_started |  |  | owner=default |
| 6051 | 2026-08-16T06:12:26.290Z | managed_process_terminal |  |  | owner=default |
| 6052 | 2026-08-16T06:12:26.543Z | proof_recorded |  |  | stage_id=check:16333285e684aa5c; status=passed; cache_hit=False; input_fingerprint=07ae1c3ee8bbaafa525b11abf1043fbd681b81feb01789484390cf52b64d31d6 |
| 6053 | 2026-08-16T06:12:26.993Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6054 | 2026-08-16T06:12:47.861Z | managed_process_admitted |  |  | owner=default |
| 6055 | 2026-08-16T06:12:48.119Z | managed_process_started |  |  | owner=default |
| 6056 | 2026-08-16T06:12:48.482Z | managed_process_terminal |  |  | owner=default |
| 6057 | 2026-08-16T06:13:00.305Z | managed_process_admitted |  |  | owner=default |
| 6058 | 2026-08-16T06:13:00.610Z | managed_process_started |  |  | owner=default |
| 6059 | 2026-08-16T06:13:01.131Z | managed_process_terminal |  |  | owner=default |
| 6060 | 2026-08-16T06:13:08.498Z | managed_process_admitted |  |  | owner=default |
| 6061 | 2026-08-16T06:13:08.911Z | managed_process_started |  |  | owner=default |
| 6062 | 2026-08-16T06:13:15.219Z | managed_process_terminal |  |  | owner=default |
| 6063 | 2026-08-16T06:13:24.078Z | managed_process_admitted |  |  | owner=default |
| 6064 | 2026-08-16T06:13:25.627Z | managed_process_started |  |  | owner=default |
| 6065 | 2026-08-16T06:13:29.333Z | managed_process_terminal |  |  | owner=default |
| 6066 | 2026-08-16T06:13:42.230Z | managed_process_admitted |  |  | owner=default |
| 6067 | 2026-08-16T06:13:43.693Z | managed_process_started |  |  | owner=default |
| 6068 | 2026-08-16T06:13:51.704Z | managed_process_terminal |  |  | owner=default |
| 6069 | 2026-08-16T06:13:58.244Z | managed_process_admitted |  |  | owner=default |
| 6070 | 2026-08-16T06:13:59.002Z | managed_process_started |  |  | owner=default |
| 6071 | 2026-08-16T06:14:05.218Z | managed_process_terminal |  |  | owner=default |
| 6072 | 2026-08-16T06:14:48.577Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6073 | 2026-08-16T06:14:49.015Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:16333285e684aa5c | passed | 07ae1c3ee8bbaafa525b11abf1043fbd681b81feb01789484390cf52b64d31d6 | False | 8447 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e4f29a39033446859439dd70ebaa91da | accepted | 597170860118a847b7e8a6f06903c37da8432d82 | b399f7fdf71a6d2b747a2390a14ebc24ef2e1a606d396de05ddfea842270a6c2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `73`
- Chain head: `f264f4df913169de534f8892f03b91141ab319567ccd6eba5a07be54baec9b1d`
