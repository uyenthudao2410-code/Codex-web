# Orchestration Wave 1

- Run: `97a1a8c55658484aa0263a0445bf3405`
- Wave: `788e8c4868d049d8b6af23528a608f59`
- Objective: Stabilize the Recovery Host -> currentMcpHealth() -> /__control/health boundary without touching foreign stale runs or production runtime. Preserve readMcpHealth compatibility, classify deterministic auth/workspace/device/protocol mismatches separately from timeout/transport/not-ready failures, expose the classification through recoveryStatus/lightweight snapshots, and ensure deterministic mismatches fail closed without destructive restart escalation while timeout/hung failures retain the existing bounded restart escalation.
- Objective revision: `1`
- Objective SHA-256: `db60f1138f120eef45c0b4cdf8934c4c3db790fe760ed9a45bbc700465a4ca58`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9`
- Worktree fingerprint: `068db68b259d7fd0cc42c929660deec0875da457caadad3c78e3bf0586bc114c`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 30559 | 2026-08-26T09:24:23.063Z | run_started |  | PREFLIGHT |  |
| 30560 | 2026-08-26T09:24:23.605Z | observation_span_recorded |  |  |  |
| 30561 | 2026-08-26T09:24:24.008Z | solution_shadow_recommended |  |  |  |
| 30562 | 2026-08-26T09:24:24.246Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 30563 | 2026-08-26T09:24:24.397Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 30564 | 2026-08-26T09:24:24.552Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 30565 | 2026-08-26T09:24:24.723Z | state_transition | READY | ROUTED | reason=route_selected |
| 30566 | 2026-08-26T09:24:24.983Z | observation_span_recorded |  |  |  |
| 30567 | 2026-08-26T09:24:26.048Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d92479bdb84e4cc1a51b4a260293bce2 |
| 30568 | 2026-08-26T09:24:26.186Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 30569 | 2026-08-26T09:24:27.444Z | patch_surface_observed |  |  |  |
| 30570 | 2026-08-26T09:24:27.763Z | observation_span_recorded |  |  |  |
| 30571 | 2026-08-26T09:24:28.068Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d92479bdb84e4cc1a51b4a260293bce2 |
| 30572 | 2026-08-26T09:24:28.217Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 30573 | 2026-08-26T09:24:29.159Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a0064c5ee7c069aef118eb151e0ced319e7916c052f5c30cbf4fa0a7030a60f0 |
| 30574 | 2026-08-26T09:24:29.846Z | managed_process_admitted |  |  | owner=default |
| 30575 | 2026-08-26T09:24:30.239Z | managed_process_started |  |  | owner=default |
| 30576 | 2026-08-26T09:24:32.101Z | managed_process_terminal |  |  | owner=default |
| 30577 | 2026-08-26T09:24:32.475Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=a0064c5ee7c069aef118eb151e0ced319e7916c052f5c30cbf4fa0a7030a60f0 |
| 30578 | 2026-08-26T09:24:32.878Z | observation_span_recorded |  |  |  |
| 30579 | 2026-08-26T09:24:33.164Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 30580 | 2026-08-26T09:24:33.349Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 30581 | 2026-08-26T09:24:33.623Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | a0064c5ee7c069aef118eb151e0ced319e7916c052f5c30cbf4fa0a7030a60f0 | False | 2969 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `98fb19a3b597a84dc18e1baf987a0f44af78d9ab23642a7d32213f59f93025fd`
