# Orchestration Wave 2

- Run: `05f7a91f494040be98960987a297fe1f`
- Wave: `67882053f2034cf9830bb01ad9718c8f`
- Objective: Implement and verify P0.3 F4 and F6 real-process tunnel recovery proofs only. First inspect electron/services/tunnelService.js plus the exact RecoveryPlaneService and RuntimeOrchestrator tunnel start/recovery seams. Add the smallest test-only local tunnel fixture that supports the production run/health invocation shape, opens a real loopback health listener owned by the fixture PID itself, reports JSON health, and makes no external/provider network calls. Then add F4 to tests/recovery-plane.test.js: start an isolated Recovery MCP + Recovery Tunnel through production RecoveryPlaneService using the fixture, record Recovery MCP PID and Tunnel PID, kill only the Tunnel PID, rerun the production ensure/recovery path, prove a different Tunnel PID is promoted, Recovery MCP PID is unchanged/alive, device identity and configured ports remain correct, the health port responds from the new Tunnel PID, and no duplicate/foreign listener is adopted. Add F6 to tests/runtime-lifecycle.test.js (or the narrowest existing primary runtime test file): run an isolated primary Coding MCP identity/process fixture plus primary Tunnel through the actual production tunnel recovery path, kill only the Tunnel PID, trigger the same recoverTunnelOnly/supervision path, prove a different Tunnel PID is running, the Coding MCP PID/workspace/device identity is unchanged/alive, and health/listener ownership is correct. Preserve all unrelated dirty UI files and all production source. If the existing production interfaces make this impossible without changing production code, stop with a concrete REPLAN reason instead of weakening ownership checks. Run git diff --check on only changed F4/F6 test/fixture files and node --test tests/recovery-plane.test.js tests/runtime-lifecycle.test.js. Report exact changed files and exact PASS/FAIL counts.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `1cf9ac7d783050efb6a9e452fa2fcc6e4c47351a6e7375d8d415e1b9c257e7a0`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13505 | 2026-08-17T10:06:37.646Z | wave_replanned |  | PREFLIGHT | reason=The prior F4/F6 wave was explicitly rejected because it was content_free with files_modified=0 and only reran existing tests. This wave changes strategy: first map the exact injectable production interfaces and writable test-only scope, then implement a PID-faithful local process fixture in a subsequent execution wave. |
| 13506 | 2026-08-17T10:06:38.694Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13507 | 2026-08-17T10:08:00.708Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13508 | 2026-08-17T10:08:22.451Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13509 | 2026-08-17T10:09:50.344Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13510 | 2026-08-17T10:10:22.112Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13511 | 2026-08-17T10:12:07.165Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13512 | 2026-08-17T10:12:07.411Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13513 | 2026-08-17T10:12:07.601Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13514 | 2026-08-17T10:12:07.802Z | state_transition | READY | ROUTED | reason=route_selected |
| 13515 | 2026-08-17T10:12:08.566Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0250c52c5cc042e9871ed14f17b215bf |
| 13516 | 2026-08-17T10:12:08.790Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13517 | 2026-08-17T10:12:09.558Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0250c52c5cc042e9871ed14f17b215bf |
| 13518 | 2026-08-17T10:12:09.775Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13519 | 2026-08-17T10:12:10.622Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2f4546c29a84a03e; input_fingerprint=ec3685073b21864f5aef19401fd7fa7be305d7ba8ce9d20c65b41f2fd6e24000 |
| 13520 | 2026-08-17T10:12:10.998Z | managed_process_admitted |  |  | owner=default |
| 13521 | 2026-08-17T10:12:11.364Z | managed_process_started |  |  | owner=default |
| 13522 | 2026-08-17T10:12:11.958Z | managed_process_terminal |  |  | owner=default |
| 13523 | 2026-08-17T10:12:12.648Z | proof_recorded |  |  | stage_id=check:2f4546c29a84a03e; status=passed; cache_hit=False; input_fingerprint=ec3685073b21864f5aef19401fd7fa7be305d7ba8ce9d20c65b41f2fd6e24000 |
| 13524 | 2026-08-17T10:12:12.907Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0b53afe189e4545973d661ecd4125eb35fab9924c9a44645c86512bce6add579 |
| 13525 | 2026-08-17T10:12:13.365Z | managed_process_admitted |  |  | owner=default |
| 13526 | 2026-08-17T10:12:13.686Z | managed_process_started |  |  | owner=default |
| 13527 | 2026-08-17T10:12:16.605Z | managed_process_terminal |  |  | owner=default |
| 13528 | 2026-08-17T10:12:18.256Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0b53afe189e4545973d661ecd4125eb35fab9924c9a44645c86512bce6add579 |
| 13529 | 2026-08-17T10:12:18.545Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13530 | 2026-08-17T10:14:39.373Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13531 | 2026-08-17T10:14:40.895Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2f4546c29a84a03e | passed | ec3685073b21864f5aef19401fd7fa7be305d7ba8ce9d20c65b41f2fd6e24000 | False | 1626 | 0 |
| verify:tests | passed | 0b53afe189e4545973d661ecd4125eb35fab9924c9a44645c86512bce6add579 | False | 4828 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 93083bf8e9914ea8a38af25c7a137070 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | ce740922f47d181784640f2cdd4099be3d2c0984314d06e5c6f365c90823b3e9 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `f9c1971a606ad27c12af5489e30e14deebeba87aba090547b56b77d63e7c4e9e`
