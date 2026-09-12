# Orchestration Wave 1

- Run: `f50672428d784bf88c8cf211d6ec7809`
- Wave: `35334d87bb4147d9a9b44aa76085f6a4`
- Objective: Make exact stale-run maintenance restart use checkpoint-free full_clean_refresh while preserving ordinary restart accepted-checkpoint authority; preserve all exact stale IDs up to the existing 16-ID bound instead of truncating the maintenance reason; validate maintenance reason structure before any mutation; add regressions proving 16 IDs survive and maintenance refresh does not require source-checkpoint authority.
- Objective revision: `1`
- Objective SHA-256: `ea82f006ba5d1284d38401222b0db3188d8b4bb2485294cc947abfe5ec318d8d`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `24186fefbdbb9c1dca450ae5e96df167be93c87e`
- Worktree fingerprint: `44bf43712788971ffd06fede4cc474d4374515acee14850242c4dd05e425f7aa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43149 | 2026-09-07T08:03:52.092Z | run_started |  | PREFLIGHT |  |
| 43150 | 2026-09-07T08:03:52.571Z | observation_span_recorded |  |  |  |
| 43151 | 2026-09-07T08:04:12.000Z | solution_shadow_recommended |  |  |  |
| 43152 | 2026-09-07T08:04:42.483Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43153 | 2026-09-07T08:04:42.693Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43154 | 2026-09-07T08:04:42.874Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 43155 | 2026-09-07T08:04:43.022Z | state_transition | READY | ROUTED | reason=route_selected |
| 43156 | 2026-09-07T08:04:43.237Z | observation_span_recorded |  |  |  |
| 43157 | 2026-09-07T08:04:43.923Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3738b70934b84d7eb5f0ea645ae5c330 |
| 43158 | 2026-09-07T08:04:44.097Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43159 | 2026-09-07T08:04:44.726Z | patch_surface_observed |  |  |  |
| 43160 | 2026-09-07T08:04:45.027Z | patch_surface_observed |  |  |  |
| 43161 | 2026-09-07T08:04:45.313Z | observation_span_recorded |  |  |  |
| 43162 | 2026-09-07T08:04:45.523Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3738b70934b84d7eb5f0ea645ae5c330 |
| 43163 | 2026-09-07T08:04:45.658Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43164 | 2026-09-07T08:04:46.274Z | proof_cache_miss |  |  | reason=cold; stage_id=check:676da3863891edd1; input_fingerprint=c57375b28371bdda67249c381696515e4b8f1c395029ed88f4a60a16b15fa272 |
| 43165 | 2026-09-07T08:04:46.623Z | managed_process_admitted |  |  | owner=default |
| 43166 | 2026-09-07T08:04:46.843Z | managed_process_started |  |  | owner=default |
| 43167 | 2026-09-07T08:04:47.251Z | managed_process_terminal |  |  | owner=default |
| 43168 | 2026-09-07T08:04:47.522Z | proof_recorded |  |  | stage_id=check:676da3863891edd1; status=passed; cache_hit=False; input_fingerprint=c57375b28371bdda67249c381696515e4b8f1c395029ed88f4a60a16b15fa272 |
| 43169 | 2026-09-07T08:04:47.676Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5fad9f7a8a0e51a0f968985a5333982fb420b9a2f473c593ee23721f72b6bf14 |
| 43170 | 2026-09-07T08:04:47.917Z | observation_span_recorded |  |  |  |
| 43171 | 2026-09-07T08:04:48.132Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 43172 | 2026-09-07T08:04:48.308Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 43173 | 2026-09-07T08:04:48.480Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:676da3863891edd1 | passed | c57375b28371bdda67249c381696515e4b8f1c395029ed88f4a60a16b15fa272 | False | 902 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `4441be1f9537d31de3bcbff08905974c894ceb0eaa816514d460942476c651e2`
