# Orchestration Wave 1

- Run: `fa636a1db1084be6a29812d6c61660c4`
- Wave: `c8772c2c4dbf40a4a20d93070ad1fc09`
- Objective: Implement the smallest H4 Codex exact-usage persistence closure on E:\DEV\Codex-web. Preserve the existing Codex App Server thread/tokenUsage/updated authority, but make it fail-closed: only complete non-negative integer inputTokens/cachedInputTokens/outputTokens/reasoningOutputTokens may be marked measured. Persist exact Codex candidate-model usage as a canonical provider UsageEvent bound to the current RUN/WAVE/delegation with provider_reported provenance and source codex_app_server:thread/tokenUsage/updated. Do not claim provider-measured monetary cost; cost may remain derived/unobserved. Missing or incomplete token usage must produce no UsageEvent, never zero. Do not change public 8-tool contract, routing authority, restart behavior, or unrelated dirty hunks. Add focused tests for exact X/Y/Z/R persistence and incomplete-token fail-closed behavior.
- Objective revision: `1`
- Objective SHA-256: `6aee0544e832b3a226794ae2a4578f482508e3650be1a59c40f833a8b42e7e31`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `ee361515c1f37d8d1ab3b29da6e5a2d5980694d057a9e83d445c7dab80a6a3bd`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36299 | 2026-09-03T05:09:43.344Z | run_started |  | PREFLIGHT |  |
| 36300 | 2026-09-03T05:09:43.715Z | observation_span_recorded |  |  |  |
| 36301 | 2026-09-03T05:09:44.110Z | solution_shadow_recommended |  |  |  |
| 36302 | 2026-09-03T05:09:46.183Z | observation_span_recorded |  |  |  |
| 36303 | 2026-09-03T05:09:46.363Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36304 | 2026-09-03T05:11:10.815Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36305 | 2026-09-03T05:11:11.007Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36306 | 2026-09-03T05:11:11.215Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36307 | 2026-09-03T05:11:11.403Z | state_transition | READY | ROUTED | reason=route_selected |
| 36308 | 2026-09-03T05:11:11.705Z | observation_span_recorded |  |  |  |
| 36309 | 2026-09-03T05:11:13.735Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ecf521c55ae64efa87d4cc988a99d976 |
| 36310 | 2026-09-03T05:11:13.913Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36311 | 2026-09-03T05:11:16.207Z | patch_surface_observed |  |  |  |
| 36312 | 2026-09-03T05:11:16.380Z | observation_span_recorded |  |  |  |
| 36313 | 2026-09-03T05:11:16.636Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ecf521c55ae64efa87d4cc988a99d976 |
| 36314 | 2026-09-03T05:11:16.811Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36315 | 2026-09-03T05:11:18.548Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0207350e260dae6495301f04ec7db5b26588e889911f716391090274bd11b878 |
| 36316 | 2026-09-03T05:11:19.313Z | managed_process_admitted |  |  | owner=default |
| 36317 | 2026-09-03T05:11:19.586Z | managed_process_started |  |  | owner=default |
| 36318 | 2026-09-03T05:12:11.145Z | managed_process_terminal |  |  | owner=default |
| 36319 | 2026-09-03T05:12:12.814Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0207350e260dae6495301f04ec7db5b26588e889911f716391090274bd11b878 |
| 36320 | 2026-09-03T05:12:14.421Z | observation_span_recorded |  |  |  |
| 36321 | 2026-09-03T05:12:14.616Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 36322 | 2026-09-03T05:13:48.682Z | managed_process_admitted |  |  | owner=default |
| 36323 | 2026-09-03T05:13:49.048Z | managed_process_started |  |  | owner=default |
| 36324 | 2026-09-03T05:13:49.642Z | managed_process_terminal |  |  | owner=default |
| 36325 | 2026-09-03T05:14:00.633Z | managed_process_admitted |  |  | owner=default |
| 36326 | 2026-09-03T05:14:01.015Z | managed_process_started |  |  | owner=default |
| 36327 | 2026-09-03T05:14:01.781Z | managed_process_terminal |  |  | owner=default |
| 36328 | 2026-09-03T05:14:16.397Z | quality_outcome_recorded |  |  |  |
| 36329 | 2026-09-03T05:14:16.677Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 36330 | 2026-09-03T05:14:16.937Z | observation_span_recorded |  |  |  |
| 36331 | 2026-09-03T05:14:17.195Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 0207350e260dae6495301f04ec7db5b26588e889911f716391090274bd11b878 | False | 53468 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f13cbf4f937944f38393b057c5dbeb98 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 5fe77d3e8d06999f420c7d38a4d4675ec1bde06401cc0230d590d0c6121acd88 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `3ad5faca539893c735915a3d6b75295bc4f42cb7f7a8ef4add8d3f3ef4525360`
