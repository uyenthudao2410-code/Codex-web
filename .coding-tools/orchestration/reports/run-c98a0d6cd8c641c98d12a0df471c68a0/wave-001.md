# Orchestration Wave 1

- Run: `c98a0d6cd8c641c98d12a0df471c68a0`
- Wave: `b5e1596beb9848ee8c75bd1915665d47`
- Objective: Apply deterministic Python PRL activation/restart-ticket source and focused Python tests. Preserve unrelated dirty work. No candidate model, no runtime restart, no ledger migration.
- Objective revision: `1`
- Objective SHA-256: `6c14fbd44d9814e347fa3cd95efe950710e534d439e47a0b2b99f8186a83daa6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `58dfd3093d7a05f6999fe93e15c94050aa51d204`
- Worktree fingerprint: `903ddaeba806d5b85268ecb55059fdd54046d297acb16a34c2229d4eb20d7d12`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43514 | 2026-09-07T10:55:00.447Z | run_started |  | PREFLIGHT |  |
| 43515 | 2026-09-07T10:55:00.833Z | observation_span_recorded |  |  |  |
| 43516 | 2026-09-07T10:55:01.014Z | solution_shadow_recommended |  |  |  |
| 43517 | 2026-09-07T10:55:01.218Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43518 | 2026-09-07T10:55:01.375Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43519 | 2026-09-07T10:55:01.537Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43520 | 2026-09-07T10:55:01.716Z | state_transition | READY | ROUTED | reason=route_selected |
| 43521 | 2026-09-07T10:55:01.867Z | observation_span_recorded |  |  |  |
| 43522 | 2026-09-07T10:55:02.666Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a0b9ade2565948a99775fd26b7770b48 |
| 43523 | 2026-09-07T10:55:02.850Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43524 | 2026-09-07T10:55:03.842Z | patch_surface_observed |  |  |  |
| 43525 | 2026-09-07T10:55:04.037Z | observation_span_recorded |  |  |  |
| 43526 | 2026-09-07T10:55:04.276Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a0b9ade2565948a99775fd26b7770b48 |
| 43527 | 2026-09-07T10:55:04.422Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43528 | 2026-09-07T10:55:05.712Z | observation_span_recorded |  |  |  |
| 43529 | 2026-09-07T10:55:05.839Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43530 | 2026-09-07T10:55:17.662Z | managed_process_admitted |  |  | owner=default |
| 43531 | 2026-09-07T10:55:17.937Z | managed_process_started |  |  | owner=default |
| 43532 | 2026-09-07T10:55:20.356Z | managed_process_terminal |  |  | owner=default |
| 43533 | 2026-09-07T10:56:57.308Z | observation_span_recorded |  |  |  |
| 43534 | 2026-09-07T10:56:57.432Z | failure_observed | ACCEPTING | ACCEPTING | reason=Do not accept yet: the focused pytest command passed, but EOCL did not register it as a canonical mutation-bearing proof for this exact RUN/WAVE. Replan to exact-adopt the current five intended files and run a supported verification command that produces a durable proof before acceptance.; failure_class=SOL_REJECTED |
| 43535 | 2026-09-07T10:56:57.584Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 43536 | 2026-09-07T10:56:57.755Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `122e27eec2059d20f212c89f57dd57177fcd48a9ab580aca22e39d95ebe8daf2`
