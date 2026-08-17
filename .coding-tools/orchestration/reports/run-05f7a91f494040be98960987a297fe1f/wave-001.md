# Orchestration Wave 1

- Run: `05f7a91f494040be98960987a297fe1f`
- Wave: `931a8d17ff7945748f79cf5e7b8a5108`
- Objective: Implement and verify P0.3 F4 and F6 real-process tunnel recovery proofs only. First inspect electron/services/tunnelService.js plus the exact RecoveryPlaneService and RuntimeOrchestrator tunnel start/recovery seams. Add the smallest test-only local tunnel fixture that supports the production run/health invocation shape, opens a real loopback health listener owned by the fixture PID itself, reports JSON health, and makes no external/provider network calls. Then add F4 to tests/recovery-plane.test.js: start an isolated Recovery MCP + Recovery Tunnel through production RecoveryPlaneService using the fixture, record Recovery MCP PID and Tunnel PID, kill only the Tunnel PID, rerun the production ensure/recovery path, prove a different Tunnel PID is promoted, Recovery MCP PID is unchanged/alive, device identity and configured ports remain correct, the health port responds from the new Tunnel PID, and no duplicate/foreign listener is adopted. Add F6 to tests/runtime-lifecycle.test.js (or the narrowest existing primary runtime test file): run an isolated primary Coding MCP identity/process fixture plus primary Tunnel through the actual production tunnel recovery path, kill only the Tunnel PID, trigger the same recoverTunnelOnly/supervision path, prove a different Tunnel PID is running, the Coding MCP PID/workspace/device identity is unchanged/alive, and health/listener ownership is correct. Preserve all unrelated dirty UI files and all production source. If the existing production interfaces make this impossible without changing production code, stop with a concrete REPLAN reason instead of weakening ownership checks. Run git diff --check on only changed F4/F6 test/fixture files and node --test tests/recovery-plane.test.js tests/runtime-lifecycle.test.js. Report exact changed files and exact PASS/FAIL counts.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `1cf9ac7d783050efb6a9e452fa2fcc6e4c47351a6e7375d8d415e1b9c257e7a0`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13477 | 2026-08-17T10:04:05.699Z | run_started |  | PREFLIGHT |  |
| 13478 | 2026-08-17T10:04:06.687Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13479 | 2026-08-17T10:04:07.031Z | managed_process_admitted |  |  | owner=default |
| 13480 | 2026-08-17T10:04:07.418Z | managed_process_started |  |  | owner=default |
| 13481 | 2026-08-17T10:04:09.184Z | managed_process_terminal |  |  | owner=default |
| 13482 | 2026-08-17T10:04:09.485Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13483 | 2026-08-17T10:04:09.703Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13484 | 2026-08-17T10:04:09.898Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13485 | 2026-08-17T10:04:10.151Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13486 | 2026-08-17T10:04:10.363Z | state_transition | READY | ROUTED | reason=route_selected |
| 13487 | 2026-08-17T10:04:11.118Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=084f8c3a85da4ef7bf27e96b5fc78e12 |
| 13488 | 2026-08-17T10:04:11.339Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13489 | 2026-08-17T10:04:12.068Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=084f8c3a85da4ef7bf27e96b5fc78e12 |
| 13490 | 2026-08-17T10:04:12.315Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13491 | 2026-08-17T10:04:12.902Z | proof_cache_miss |  |  | reason=cold; stage_id=check:af6085c4efd56568; input_fingerprint=626d9564e1525e78c8c7dff43cc3fedc3435f25d3c489286efb2e7cffc47ea11 |
| 13492 | 2026-08-17T10:04:13.211Z | managed_process_admitted |  |  | owner=default |
| 13493 | 2026-08-17T10:04:13.538Z | managed_process_started |  |  | owner=default |
| 13494 | 2026-08-17T10:04:14.082Z | managed_process_terminal |  |  | owner=default |
| 13495 | 2026-08-17T10:04:14.518Z | proof_recorded |  |  | stage_id=check:af6085c4efd56568; status=passed; cache_hit=False; input_fingerprint=626d9564e1525e78c8c7dff43cc3fedc3435f25d3c489286efb2e7cffc47ea11 |
| 13496 | 2026-08-17T10:04:14.716Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ab9ffee645bfe6aac201be78d2ca1f91f25230bb2f74ac5ee700066f9ff900ce |
| 13497 | 2026-08-17T10:04:15.141Z | managed_process_admitted |  |  | owner=default |
| 13498 | 2026-08-17T10:04:15.561Z | managed_process_started |  |  | owner=default |
| 13499 | 2026-08-17T10:04:17.118Z | managed_process_terminal |  |  | owner=default |
| 13500 | 2026-08-17T10:04:18.518Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ab9ffee645bfe6aac201be78d2ca1f91f25230bb2f74ac5ee700066f9ff900ce |
| 13501 | 2026-08-17T10:04:18.733Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13502 | 2026-08-17T10:06:16.558Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject semantic completion for F4/F6. Durable audit is content_free with files_modified=0 and no implementation delta; the execution lease had allowed_paths=[] and the workflow only reran existing tests. Although git diff --check and the focused Node suite passed, that does not satisfy the requested new real-process PID proofs for F4 Recovery Tunnel replacement and F6 primary Tunnel replacement. Replan must explicitly add scoped test-only fixture/tests (or stop with a concrete impossibility reason) while preserving unrelated UI work and without weakening ownership/listener-PID checks or changing production source absent a reproduced defect.; failure_class=SOL_REJECTED |
| 13503 | 2026-08-17T10:06:16.763Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 13504 | 2026-08-17T10:06:16.962Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:af6085c4efd56568 | passed | 626d9564e1525e78c8c7dff43cc3fedc3435f25d3c489286efb2e7cffc47ea11 | False | 1244 | 0 |
| verify:tests | passed | ab9ffee645bfe6aac201be78d2ca1f91f25230bb2f74ac5ee700066f9ff900ce | False | 3281 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `f9c1971a606ad27c12af5489e30e14deebeba87aba090547b56b77d63e7c4e9e`
