# Orchestration Wave 1

- Run: `89a8aced08554828a6e13cd07db8ea3a`
- Wave: `8d5f8d5ff17e4c768bd8a78be16173d2`
- Objective: Map and close P0.3 fault-matrix cases F4 and F6 exactly as defined by docs/PRODUCTION_CLOSURE_ROLLOUT.md. Identify the production Recovery Tunnel and primary Tunnel lifecycle/restart code paths and existing tests. Design the smallest test-only real-process fixture that runs under the production services without contacting an external provider: kill Recovery Tunnel and require a new tunnel PID while Recovery MCP PID remains unchanged; kill primary Tunnel and require a new tunnel PID while Coding MCP PID remains unchanged. Preserve device identity, ports, descriptors, fail-closed ownership, and unrelated UI/local changes. Do not modify production code unless a reproducible product defect is found.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `a6bb8a1978cde07bd8c75b99b5b6ce84cc008c4103aae639eacf5bd9aabca06d`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13435 | 2026-08-17T10:00:46.059Z | run_started |  | PREFLIGHT |  |
| 13436 | 2026-08-17T10:00:47.053Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13437 | 2026-08-17T10:00:48.111Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13438 | 2026-08-17T10:00:48.526Z | managed_process_admitted |  |  | owner=default |
| 13439 | 2026-08-17T10:00:48.882Z | managed_process_started |  |  | owner=default |
| 13440 | 2026-08-17T10:00:49.508Z | managed_process_terminal |  |  | owner=default |
| 13441 | 2026-08-17T10:00:49.702Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13442 | 2026-08-17T10:00:49.875Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13443 | 2026-08-17T10:00:50.075Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13444 | 2026-08-17T10:00:50.287Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13445 | 2026-08-17T10:00:50.475Z | state_transition | READY | ROUTED | reason=route_selected |
| 13446 | 2026-08-17T10:00:51.084Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bcf736dd189e45578e1ffe2d26b504b8 |
| 13447 | 2026-08-17T10:00:51.258Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13448 | 2026-08-17T10:00:51.891Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bcf736dd189e45578e1ffe2d26b504b8 |
| 13449 | 2026-08-17T10:00:52.041Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13450 | 2026-08-17T10:00:52.634Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=12fcc05057a12781beaf26bf45b4427f12cfdd0736312b6b604355640fe800d5 |
| 13451 | 2026-08-17T10:00:53.024Z | managed_process_admitted |  |  | owner=default |
| 13452 | 2026-08-17T10:00:53.298Z | managed_process_started |  |  | owner=default |
| 13453 | 2026-08-17T10:00:53.749Z | managed_process_terminal |  |  | owner=default |
| 13454 | 2026-08-17T10:00:55.212Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=12fcc05057a12781beaf26bf45b4427f12cfdd0736312b6b604355640fe800d5 |
| 13455 | 2026-08-17T10:00:55.472Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13456 | 2026-08-17T10:01:48.237Z | failure_observed | ACCEPTING | ACCEPTING | reason=Wave produced zero modified files and therefore did not satisfy the user's requested visible UI fix. The screenshot still requires a non-collapsing Executive Summary, readable vertical Execution Hub layout, and materially larger typography.; failure_class=SOL_REJECTED |
| 13457 | 2026-08-17T10:01:48.465Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 13458 | 2026-08-17T10:01:48.705Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 12fcc05057a12781beaf26bf45b4427f12cfdd0736312b6b604355640fe800d5 | False | 2077 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `49f3c52210e5191be4a1a33ef6f9f160f0978d72b73d4a275740bd521811e6f4`
