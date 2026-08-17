# Orchestration Wave 1

- Run: `fb8dde2f146146b78391cd75ea7c6cb0`
- Wave: `1bf7d976ea534024831b87bf4812cdd5`
- Objective: Map the living-plan P0.3 F1-F9 matrix to exact current proof strength without changing source. For each F1-F9, identify the strongest exact test/script and whether it is real process, isolated fixture, deterministic unit, source/static assertion, packaged/installed acceptance, or external-only. Pay particular attention to F2 Recovery Host PID exit -> Supervisor recreation; F4 Recovery Tunnel PID exit -> new Tunnel PID while Recovery MCP PID stays; F5 primary Coding MCP PID exit -> current RuntimeOrchestrator policy and no foreign adoption; F6 primary Tunnel PID exit -> tunnel-only recovery with Coding MCP PID preserved; F7 stale Recovery Host lock/descriptor replacement; F8 foreign/live listener/owner fail-closed; F1 and accepted F3/F9 evidence. Identify the smallest genuine test additions needed to meet docs/PRODUCTION_CLOSURE_ROLLOUT.md without external tunnel/provider credentials and without touching the active development runtime. Also locate any existing packaged/isolated recovery smoke harness that can cover F2/F4/F6.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `b20109daa7b486c64b9952d3ccac23f0f2b80d2ae260352c1fa1350686aad008`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13295 | 2026-08-17T09:41:20.185Z | run_started |  | PREFLIGHT |  |
| 13296 | 2026-08-17T09:41:21.409Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13297 | 2026-08-17T09:41:40.620Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13298 | 2026-08-17T09:41:59.240Z | managed_process_admitted |  |  | owner=default |
| 13299 | 2026-08-17T09:41:59.523Z | managed_process_started |  |  | owner=default |
| 13300 | 2026-08-17T09:42:00.011Z | managed_process_terminal |  |  | owner=default |
| 13301 | 2026-08-17T09:42:23.047Z | managed_process_admitted |  |  | owner=default |
| 13302 | 2026-08-17T09:42:23.689Z | managed_process_started |  |  | owner=default |
| 13303 | 2026-08-17T09:42:24.311Z | managed_process_terminal |  |  | owner=default |
| 13304 | 2026-08-17T09:43:04.417Z | managed_process_admitted |  |  | owner=default |
| 13305 | 2026-08-17T09:43:06.107Z | managed_process_started |  |  | owner=default |
| 13306 | 2026-08-17T09:43:07.269Z | managed_process_terminal |  |  | owner=default |
| 13307 | 2026-08-17T09:43:52.325Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13308 | 2026-08-17T09:44:06.784Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13309 | 2026-08-17T09:44:07.533Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13310 | 2026-08-17T09:44:08.401Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13311 | 2026-08-17T09:44:08.646Z | state_transition | READY | ROUTED | reason=route_selected |
| 13312 | 2026-08-17T09:44:09.823Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7f74072d510f41668af14bc887943319 |
| 13313 | 2026-08-17T09:44:10.107Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13314 | 2026-08-17T09:44:12.714Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7f74072d510f41668af14bc887943319 |
| 13315 | 2026-08-17T09:44:13.419Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13316 | 2026-08-17T09:44:14.726Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9ec42d504853ed232563dd04492638ef9f57d3ad071dc047d44abaed515adb44 |
| 13317 | 2026-08-17T09:44:15.615Z | managed_process_admitted |  |  | owner=default |
| 13318 | 2026-08-17T09:44:16.450Z | managed_process_started |  |  | owner=default |
| 13319 | 2026-08-17T09:44:17.550Z | managed_process_terminal |  |  | owner=default |
| 13320 | 2026-08-17T09:44:20.374Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9ec42d504853ed232563dd04492638ef9f57d3ad071dc047d44abaed515adb44 |
| 13321 | 2026-08-17T09:44:21.305Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13322 | 2026-08-17T09:46:26.381Z | managed_process_admitted |  |  | owner=default |
| 13323 | 2026-08-17T09:46:26.814Z | managed_process_started |  |  | owner=default |
| 13324 | 2026-08-17T09:46:27.415Z | managed_process_terminal |  |  | owner=default |
| 13325 | 2026-08-17T09:48:45.326Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13326 | 2026-08-17T09:48:45.815Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 9ec42d504853ed232563dd04492638ef9f57d3ad071dc047d44abaed515adb44 | False | 4672 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1ab485ff88ce445fb6cf37d50ef32a98 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 3993de7151e27da2a922fe0a1a28d25e17e0acce527a9cadd36178e74fb55f67 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `10740a0a039045339cb38b4083098020b12e4af03a74d86dc6ab2cd045638b95`
