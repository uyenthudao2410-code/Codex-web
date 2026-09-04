# Orchestration Wave 1

- Run: `1791781b8c1a44bfbbdcbe5fa3251675`
- Wave: `e03a81e1141249b4a05d54ccc28fc116`
- Objective: G2-P13 provenance closure ONLY for exact current resources/coding-tools-mcp/coding_tools_mcp/agent_candidate.py SHA-256 169915ff66d161d3faf35e6763c52ea21e4cc620433316885dc73ab20edc31d0. Adopt the exact existing file without changing source bytes. Causal objective: measured Codex candidate economics are persisted as canonical UsageEvent only when exact RUN, WAVE, and delegation identity are all present and consistent; incomplete/mismatched identity or non-exact usage fail closed and must not fabricate or reattribute usage. resources/coding-tools-mcp/tests/test_execution_hub.py is ACCEPTED_CURRENT focused oracle context only and must not be adopted or modified. Preserve dirty worktree and all .coding-tools evidence. No direct SQLite, stale-RUN reconciliation, bulk-adopt, other source path, synthetic Problems/outcomes, reset/restore/clean/rebase, secret output, commit/push/tag/release/publish/deploy.
- Objective revision: `1`
- Objective SHA-256: `f2eb63500640c631c6d42b3cc320a604797adcf0dd5cc1853f6e364ba4ce9b7e`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38468 | 2026-09-03T18:09:38.790Z | run_started |  | PREFLIGHT |  |
| 38469 | 2026-09-03T18:09:39.211Z | observation_span_recorded |  |  |  |
| 38470 | 2026-09-03T18:09:40.177Z | observation_span_recorded |  |  |  |
| 38471 | 2026-09-03T18:09:40.413Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38472 | 2026-09-03T18:09:40.589Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38473 | 2026-09-03T18:09:40.748Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38474 | 2026-09-03T18:09:40.948Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38475 | 2026-09-03T18:09:41.132Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38476 | 2026-09-03T18:09:41.299Z | state_transition | READY | ROUTED | reason=route_selected |
| 38477 | 2026-09-03T18:09:41.525Z | observation_span_recorded |  |  |  |
| 38478 | 2026-09-03T18:09:42.565Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=dc9b5e9fc18c48f8b05d940b84b7936b |
| 38479 | 2026-09-03T18:09:42.765Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38480 | 2026-09-03T18:09:43.710Z | existing_file_adoption_observed |  |  |  |
| 38481 | 2026-09-03T18:09:43.947Z | observation_span_recorded |  |  |  |
| 38482 | 2026-09-03T18:09:44.282Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=dc9b5e9fc18c48f8b05d940b84b7936b |
| 38483 | 2026-09-03T18:09:44.440Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38484 | 2026-09-03T18:09:45.436Z | proof_cache_miss |  |  | reason=cold; stage_id=check:75d2d3b86a344af0; input_fingerprint=3a490913fe9ee607debb53bfa1dff9eb3b54fde19a72ae8f3305b2b96fa74afa |
| 38485 | 2026-09-03T18:09:45.849Z | managed_process_admitted |  |  | owner=default |
| 38486 | 2026-09-03T18:09:46.281Z | managed_process_started |  |  | owner=default |
| 38487 | 2026-09-03T18:09:46.781Z | managed_process_terminal |  |  | owner=default |
| 38488 | 2026-09-03T18:09:47.217Z | proof_recorded |  |  | stage_id=check:75d2d3b86a344af0; status=passed; cache_hit=False; input_fingerprint=3a490913fe9ee607debb53bfa1dff9eb3b54fde19a72ae8f3305b2b96fa74afa |
| 38489 | 2026-09-03T18:09:47.398Z | proof_cache_miss |  |  | reason=cold; stage_id=check:83b5aa39f0e5ec05; input_fingerprint=9c716448afaf812222122ff96dea5356c1485851d1b594b71e536ec4d4786a34 |
| 38490 | 2026-09-03T18:09:47.765Z | managed_process_admitted |  |  | owner=default |
| 38491 | 2026-09-03T18:09:48.108Z | managed_process_started |  |  | owner=default |
| 38492 | 2026-09-03T18:09:52.598Z | managed_process_terminal |  |  | owner=default |
| 38493 | 2026-09-03T18:09:53.015Z | proof_recorded |  |  | stage_id=check:83b5aa39f0e5ec05; status=passed; cache_hit=False; input_fingerprint=9c716448afaf812222122ff96dea5356c1485851d1b594b71e536ec4d4786a34 |
| 38494 | 2026-09-03T18:09:53.254Z | observation_span_recorded |  |  |  |
| 38495 | 2026-09-03T18:09:53.481Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38496 | 2026-09-03T18:10:52.942Z | quality_outcome_recorded |  |  |  |
| 38497 | 2026-09-03T18:10:53.163Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38498 | 2026-09-03T18:10:53.463Z | observation_span_recorded |  |  |  |
| 38499 | 2026-09-03T18:10:53.679Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:75d2d3b86a344af0 | passed | 3a490913fe9ee607debb53bfa1dff9eb3b54fde19a72ae8f3305b2b96fa74afa | False | 1359 | 0 |
| check:83b5aa39f0e5ec05 | passed | 9c716448afaf812222122ff96dea5356c1485851d1b594b71e536ec4d4786a34 | False | 5286 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 9b74a2a9c8eb49d9a276486dbdd144a2 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 720bcbae6544c38a66f25012307d12ccabefa321fc81f6c4b4318d6c1bb3a2eb | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `1997a6ea85da847216cb8d680367ec944add4dd03017685af5f1295748958955`
