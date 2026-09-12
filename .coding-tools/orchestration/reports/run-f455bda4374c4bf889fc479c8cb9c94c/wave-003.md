# Orchestration Wave 3

- Run: `f455bda4374c4bf889fc479c8cb9c94c`
- Wave: `e3b52b2347844408811cab3a036b1a74`
- Objective: Natural #20 candidate diagnostic: use the repository's immutable LedgerFacts reader rather than shell-search heuristics to obtain exact accepted-cohort generic failure/replan pairs. No source mutation.
- Objective revision: `3`
- Objective SHA-256: `d0517412b607623a361cd2f6f4465e800b2c731512d275b6139df4b1d56bf870`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `106a86d0fc02094d1f8459e3f2182db3f4f50042902f6d7f0f2dd641f0396fe8`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47361 | 2026-09-10T08:36:59.817Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 located the canonical reader family; its second rg returned exit 1 only because scripts do not contain the literal event names. Change strategy to inspect the exact LedgerFacts loader and existing report entrypoints, then invoke an existing read path instead of searching for literals. |
| 47362 | 2026-09-10T08:37:00.001Z | observation_span_recorded |  |  |  |
| 47363 | 2026-09-10T08:37:05.338Z | observation_span_recorded |  |  |  |
| 47364 | 2026-09-10T08:37:05.553Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47365 | 2026-09-10T08:37:56.322Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47366 | 2026-09-10T08:37:56.524Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47367 | 2026-09-10T08:37:56.717Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 47368 | 2026-09-10T08:37:56.893Z | state_transition | READY | ROUTED | reason=route_selected |
| 47369 | 2026-09-10T08:37:57.133Z | observation_span_recorded |  |  |  |
| 47370 | 2026-09-10T08:37:58.041Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9788b0ff49d24d6faa5561d96bb15e53 |
| 47371 | 2026-09-10T08:37:58.243Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47372 | 2026-09-10T08:37:59.264Z | observation_span_recorded |  |  |  |
| 47373 | 2026-09-10T08:37:59.574Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9788b0ff49d24d6faa5561d96bb15e53 |
| 47374 | 2026-09-10T08:37:59.724Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47375 | 2026-09-10T08:38:00.574Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5b036058348df6c8; input_fingerprint=a2debd1be8276b006806a0ed0c171292906eeca6e6e8997da910f7ef68579e5c |
| 47376 | 2026-09-10T08:38:00.940Z | managed_process_admitted |  |  | owner=default |
| 47377 | 2026-09-10T08:38:01.290Z | managed_process_started |  |  | owner=default |
| 47378 | 2026-09-10T08:38:01.718Z | managed_process_terminal |  |  | owner=default |
| 47379 | 2026-09-10T08:38:02.099Z | proof_recorded |  |  | stage_id=check:5b036058348df6c8; status=failed; cache_hit=False; input_fingerprint=a2debd1be8276b006806a0ed0c171292906eeca6e6e8997da910f7ef68579e5c |
| 47380 | 2026-09-10T08:38:02.293Z | observation_span_recorded |  |  |  |
| 47381 | 2026-09-10T08:38:02.493Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 47382 | 2026-09-10T08:38:02.673Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 47383 | 2026-09-10T08:38:02.857Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5b036058348df6c8 | failed | a2debd1be8276b006806a0ed0c171292906eeca6e6e8997da910f7ef68579e5c | False | 1178 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `95dbefd4b89c56d59d1248e254ced9095acaca4fdbc0f70baaf619481bec7b52`
