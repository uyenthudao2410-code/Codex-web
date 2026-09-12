# Orchestration Wave 2

- Run: `4a9244a2ed1f41d49856e44da6886bd4`
- Wave: `bf84f47be81e4fa1b1866c7e373bb101`
- Objective: Validate and accept the exact existing allow-acceptance-pending verification packet.
- Objective revision: `1`
- Objective SHA-256: `e6c3d02303a7dc99982d34b4a62ddd982bf28a01ae696faa2d958bd8c61b230d`
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
| 44107 | 2026-09-08T17:11:46.270Z | wave_replanned |  | PREFLIGHT | reason=Correct the command working-directory contract after the pre-execution filesystem_escape rejection: run all proofs from repository root without parent-path segments; source bytes, objective, deterministic route, ownership, and seven-file adoption scope are unchanged. |
| 44108 | 2026-09-08T17:11:46.620Z | observation_span_recorded |  |  |  |
| 44109 | 2026-09-08T17:11:46.859Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44110 | 2026-09-08T17:11:47.041Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44111 | 2026-09-08T17:11:47.256Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44112 | 2026-09-08T17:11:47.423Z | state_transition | READY | ROUTED | reason=route_selected |
| 44113 | 2026-09-08T17:11:47.612Z | observation_span_recorded |  |  |  |
| 44114 | 2026-09-08T17:11:48.508Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3d9d8277d2d24211b55b26596d90c57d |
| 44115 | 2026-09-08T17:11:48.655Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44116 | 2026-09-08T17:11:49.482Z | existing_file_adoption_observed |  |  |  |
| 44117 | 2026-09-08T17:11:49.666Z | observation_span_recorded |  |  |  |
| 44118 | 2026-09-08T17:11:49.969Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3d9d8277d2d24211b55b26596d90c57d |
| 44119 | 2026-09-08T17:11:50.112Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44120 | 2026-09-08T17:11:50.994Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5895b0eb8e5499f7; input_fingerprint=5bc502270c717f436c0540247e74a51b3237079d7cff71d1d2083c25293806e2 |
| 44121 | 2026-09-08T17:11:51.457Z | managed_process_admitted |  |  | owner=default |
| 44122 | 2026-09-08T17:11:51.757Z | managed_process_started |  |  | owner=default |
| 44123 | 2026-09-08T17:12:01.999Z | managed_process_terminal |  |  | owner=default |
| 44124 | 2026-09-08T17:12:02.414Z | proof_recorded |  |  | stage_id=check:5895b0eb8e5499f7; status=passed; cache_hit=False; input_fingerprint=5bc502270c717f436c0540247e74a51b3237079d7cff71d1d2083c25293806e2 |
| 44125 | 2026-09-08T17:12:02.599Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d676b31c08528228; input_fingerprint=68923bae856742d85c49e0387ffa2f60efe1767c7ca1ae77f6bdba9d585167db |
| 44126 | 2026-09-08T17:12:02.953Z | managed_process_admitted |  |  | owner=default |
| 44127 | 2026-09-08T17:12:03.257Z | managed_process_started |  |  | owner=default |
| 44128 | 2026-09-08T17:13:13.902Z | managed_process_terminal |  |  | owner=default |
| 44129 | 2026-09-08T17:13:14.256Z | proof_recorded |  |  | stage_id=check:d676b31c08528228; status=passed; cache_hit=False; input_fingerprint=68923bae856742d85c49e0387ffa2f60efe1767c7ca1ae77f6bdba9d585167db |
| 44130 | 2026-09-08T17:13:14.491Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e9e15aebd64c2071; input_fingerprint=38362c466be881a630d76f16c89f8a0d819a30455616a4bc76df96a6b5ef4c68 |
| 44131 | 2026-09-08T17:13:14.893Z | managed_process_admitted |  |  | owner=default |
| 44132 | 2026-09-08T17:13:15.208Z | managed_process_started |  |  | owner=default |
| 44133 | 2026-09-08T17:13:15.667Z | managed_process_terminal |  |  | owner=default |
| 44134 | 2026-09-08T17:13:16.080Z | proof_recorded |  |  | stage_id=check:e9e15aebd64c2071; status=passed; cache_hit=False; input_fingerprint=38362c466be881a630d76f16c89f8a0d819a30455616a4bc76df96a6b5ef4c68 |
| 44135 | 2026-09-08T17:13:16.295Z | observation_span_recorded |  |  |  |
| 44136 | 2026-09-08T17:13:16.462Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 44137 | 2026-09-08T17:16:40.773Z | quality_outcome_recorded |  |  |  |
| 44138 | 2026-09-08T17:16:40.963Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 44139 | 2026-09-08T17:16:41.215Z | observation_span_recorded |  |  |  |
| 44140 | 2026-09-08T17:16:41.416Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5895b0eb8e5499f7 | passed | 5bc502270c717f436c0540247e74a51b3237079d7cff71d1d2083c25293806e2 | False | 11078 | 0 |
| check:d676b31c08528228 | passed | 68923bae856742d85c49e0387ffa2f60efe1767c7ca1ae77f6bdba9d585167db | False | 71338 | 0 |
| check:e9e15aebd64c2071 | passed | 38362c466be881a630d76f16c89f8a0d819a30455616a4bc76df96a6b5ef4c68 | False | 1164 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f081356536574b309f17a74159058495 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | cfe177114eb66f0f5ba4c187ac9f7b7901d32c536b9f3f2d40821638cc005d87 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `366c89da4c626046dbd5fdcd98a4d625b85ac670c147893e1909011bf60e87e0`
