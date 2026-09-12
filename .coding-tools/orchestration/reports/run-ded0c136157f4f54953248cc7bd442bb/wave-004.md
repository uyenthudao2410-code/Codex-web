# Orchestration Wave 4

- Run: `ded0c136157f4f54953248cc7bd442bb`
- Wave: `0f0209d5bccd4b8d900d5681a5c37a8b`
- Objective: Converge Recovery Host and Coding MCP component state without source writes by no-patch provenance adoption of the runtime-observed Git-dirty subset and exact controller attestation of all 26 current component-file bytes, with fresh bounded deterministic proof covering both runtime components.
- Objective revision: `1`
- Objective SHA-256: `c2cd91d8e4895328f5c5bbcef1b9125cadf5f87d6b23062146ebfefb3eee22b3`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44382 | 2026-09-08T18:28:58.572Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance of wave cc61907f1ec14b758b8ed90934d4762a exposed a 12-path dirty-boundary mismatch: app_server_persistence.py and continuation_contract.py were pre-existing dirty acceptance paths but omitted from that wave's lease allowed_paths and durable no-write adoption surface. Replan the same RUN with all 12 exact pre-existing dirty paths in lease/adoption scope, preserve the exact 26-file acceptance boundary, do not change source bytes, and use only exact-byte no-write adoption plus bounded proof. |
| 44383 | 2026-09-08T18:28:58.973Z | observation_span_recorded |  |  |  |
| 44384 | 2026-09-08T18:28:59.761Z | observation_span_recorded |  |  |  |
| 44385 | 2026-09-08T18:28:59.973Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 44386 | 2026-09-08T18:30:19.180Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44387 | 2026-09-08T18:30:19.378Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44388 | 2026-09-08T18:30:19.694Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44389 | 2026-09-08T18:30:19.877Z | state_transition | READY | ROUTED | reason=route_selected |
| 44390 | 2026-09-08T18:30:20.184Z | observation_span_recorded |  |  |  |
| 44391 | 2026-09-08T18:30:21.021Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=365b23d560a648c8b76f923e5929a0c1 |
| 44392 | 2026-09-08T18:30:21.218Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44393 | 2026-09-08T18:30:21.987Z | existing_file_adoption_observed |  |  |  |
| 44394 | 2026-09-08T18:30:22.260Z | observation_span_recorded |  |  |  |
| 44395 | 2026-09-08T18:30:22.544Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=365b23d560a648c8b76f923e5929a0c1 |
| 44396 | 2026-09-08T18:30:22.783Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44397 | 2026-09-08T18:30:23.489Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6abdfef6bfb336da; input_fingerprint=31a19c7e3a1c0f6291bd9a148f13b2a3d6ff196f45e670c84a9894713bf6bd4e |
| 44398 | 2026-09-08T18:30:23.831Z | managed_process_admitted |  |  | owner=default |
| 44399 | 2026-09-08T18:30:24.144Z | managed_process_started |  |  | owner=default |
| 44400 | 2026-09-08T18:30:41.654Z | managed_process_terminal |  |  | owner=default |
| 44401 | 2026-09-08T18:30:41.965Z | proof_recorded |  |  | stage_id=check:6abdfef6bfb336da; status=passed; cache_hit=False; input_fingerprint=31a19c7e3a1c0f6291bd9a148f13b2a3d6ff196f45e670c84a9894713bf6bd4e |
| 44402 | 2026-09-08T18:30:42.151Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:60bca7789309e0ae; input_fingerprint=ecbb18a141260690d000f7042576cf39e8747dacf9c0b564dccbb1c8f6366bcd |
| 44403 | 2026-09-08T18:30:42.551Z | managed_process_admitted |  |  | owner=default |
| 44404 | 2026-09-08T18:30:42.873Z | managed_process_started |  |  | owner=default |
| 44405 | 2026-09-08T18:30:43.293Z | managed_process_terminal |  |  | owner=default |
| 44406 | 2026-09-08T18:30:43.612Z | proof_recorded |  |  | stage_id=check:60bca7789309e0ae; status=passed; cache_hit=False; input_fingerprint=ecbb18a141260690d000f7042576cf39e8747dacf9c0b564dccbb1c8f6366bcd |
| 44407 | 2026-09-08T18:30:43.800Z | observation_span_recorded |  |  |  |
| 44408 | 2026-09-08T18:30:43.978Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44409 | 2026-09-08T18:31:28.118Z | managed_process_admitted |  |  | owner=default |
| 44410 | 2026-09-08T18:31:28.370Z | managed_process_started |  |  | owner=default |
| 44411 | 2026-09-08T18:31:28.898Z | managed_process_terminal |  |  | owner=default |
| 44412 | 2026-09-08T18:31:39.115Z | managed_process_admitted |  |  | owner=default |
| 44413 | 2026-09-08T18:31:39.466Z | managed_process_started |  |  | owner=default |
| 44414 | 2026-09-08T18:31:39.948Z | managed_process_terminal |  |  | owner=default |
| 44415 | 2026-09-08T18:31:48.398Z | managed_process_admitted |  |  | owner=default |
| 44416 | 2026-09-08T18:31:48.987Z | managed_process_started |  |  | owner=default |
| 44417 | 2026-09-08T18:31:49.465Z | managed_process_terminal |  |  | owner=default |
| 44418 | 2026-09-08T18:31:58.604Z | managed_process_admitted |  |  | owner=default |
| 44419 | 2026-09-08T18:31:58.950Z | managed_process_started |  |  | owner=default |
| 44420 | 2026-09-08T18:31:59.401Z | managed_process_terminal |  |  | owner=default |
| 44421 | 2026-09-08T18:32:07.684Z | managed_process_admitted |  |  | owner=default |
| 44422 | 2026-09-08T18:32:08.017Z | managed_process_started |  |  | owner=default |
| 44423 | 2026-09-08T18:32:08.573Z | managed_process_terminal |  |  | owner=default |
| 44424 | 2026-09-08T18:32:16.283Z | managed_process_admitted |  |  | owner=default |
| 44425 | 2026-09-08T18:32:16.892Z | managed_process_started |  |  | owner=default |
| 44426 | 2026-09-08T18:32:17.442Z | managed_process_terminal |  |  | owner=default |
| 44427 | 2026-09-08T18:32:42.093Z | quality_outcome_recorded |  |  |  |
| 44428 | 2026-09-08T18:32:42.234Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44429 | 2026-09-08T18:32:42.514Z | observation_span_recorded |  |  |  |
| 44430 | 2026-09-08T18:32:42.717Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6abdfef6bfb336da | passed | 31a19c7e3a1c0f6291bd9a148f13b2a3d6ff196f45e670c84a9894713bf6bd4e | False | 18163 | 0 |
| check:60bca7789309e0ae | passed | ecbb18a141260690d000f7042576cf39e8747dacf9c0b564dccbb1c8f6366bcd | False | 1096 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| eacee8edd41e4a77a2fe226a92ccfdf8 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 509c3673d700561689b5a24a32d58a48fbd48c2554dae883028f95241d22b052 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `168`
- Chain head: `23362491c5805f3969b52278a3f6c35b09a28a327a3b674d97f7b5982b40bc9d`
