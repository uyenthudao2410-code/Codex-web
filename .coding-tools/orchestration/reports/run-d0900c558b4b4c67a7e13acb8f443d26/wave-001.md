# Orchestration Wave 1

- Run: `d0900c558b4b4c67a7e13acb8f443d26`
- Wave: `8760c4efe69c4de9ac5063d2e0a860e1`
- Objective: Remove the now-unreachable retired COMPATIBLE_ACKNOWLEDGED presentation branch from renderer/app.js. Preserve the normalization that maps any stale persisted retired state to UNAVAILABLE. No other behavior change.
- Objective revision: `1`
- Objective SHA-256: `19b4b4a1380cbbafd38e0115116580836fa6042472e67feff4eeb5236515aec8`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `0557afa6c3aa3e02c2664d312b860973f28d3fc5`
- Worktree fingerprint: `2dbc102ba8fd6b3bb74a1076a28ed7dee062e8a69230d71c245a48b94aa81a44`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 29755 | 2026-08-25T15:08:36.817Z | run_started |  | PREFLIGHT |  |
| 29756 | 2026-08-25T15:08:37.071Z | observation_span_recorded |  |  |  |
| 29757 | 2026-08-25T15:08:37.229Z | solution_shadow_recommended |  |  |  |
| 29758 | 2026-08-25T15:08:37.976Z | observation_span_recorded |  |  |  |
| 29759 | 2026-08-25T15:08:38.069Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 29760 | 2026-08-25T15:08:38.210Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 29761 | 2026-08-25T15:08:38.329Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 29762 | 2026-08-25T15:08:38.452Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 29763 | 2026-08-25T15:08:38.570Z | state_transition | READY | ROUTED | reason=route_selected |
| 29764 | 2026-08-25T15:08:38.713Z | observation_span_recorded |  |  |  |
| 29765 | 2026-08-25T15:08:39.503Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a68ea8690dac424d87a1da96d9858081 |
| 29766 | 2026-08-25T15:08:39.618Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 29767 | 2026-08-25T15:08:40.394Z | patch_surface_observed |  |  |  |
| 29768 | 2026-08-25T15:08:40.513Z | observation_span_recorded |  |  |  |
| 29769 | 2026-08-25T15:08:40.720Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a68ea8690dac424d87a1da96d9858081 |
| 29770 | 2026-08-25T15:08:40.835Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 29771 | 2026-08-25T15:08:41.553Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=645cceff62c9ebc8ef521c71364699bf0f97caea3185a2a94cee6b168e70cc92 |
| 29772 | 2026-08-25T15:08:41.892Z | managed_process_admitted |  |  | owner=default |
| 29773 | 2026-08-25T15:08:42.144Z | managed_process_started |  |  | owner=default |
| 29774 | 2026-08-25T15:08:43.538Z | managed_process_terminal |  |  | owner=default |
| 29775 | 2026-08-25T15:08:44.623Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=645cceff62c9ebc8ef521c71364699bf0f97caea3185a2a94cee6b168e70cc92 |
| 29776 | 2026-08-25T15:08:45.487Z | observation_span_recorded |  |  |  |
| 29777 | 2026-08-25T15:08:45.693Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 30503 | 2026-08-26T08:23:20.454Z | state_transition | ACCEPTING | ABORTED | reason=Superseded by later source commit b408d985e1097d738dcf4cf2cebe2cbcfd840353; old proof no longer attests current bytes, so terminalize exact run without acceptance. |
| 30504 | 2026-08-26T08:23:20.836Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 645cceff62c9ebc8ef521c71364699bf0f97caea3185a2a94cee6b168e70cc92 | False | 2750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `b032075e9b9f249f599374de0f77d0b697ad3157fdfaecd78a9c86a5e9edacdc`
