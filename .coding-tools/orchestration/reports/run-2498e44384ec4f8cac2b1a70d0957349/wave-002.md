# Orchestration Wave 2

- Run: `2498e44384ec4f8cac2b1a70d0957349`
- Wave: `8d0547393c034f8f9da4366bc98dc38b`
- Objective: Proof-only REPLAN for the already integrated recovery and new-machine activation fix. Adopt the exact eight current source/test files by SHA-256 without changing bytes, then create canonical EOCL proof by running the combined Recovery Host/userData/recycled-PID Node tests and full activation/stateless HTTP Python tests. No additional implementation changes.
- Objective revision: `2`
- Objective SHA-256: `9e6d4a8f8cb1bb585bf87e9330cd0ce0994c0ef6aa0cacb3969405d47920caf1`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `573b6ff5a5ff2509288c9656e18fd375f1ab32d3`
- Worktree fingerprint: `b2e43a13319453167ed05d2e758572f5bb196d37699edc5c82582dd06eabb565`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41262 | 2026-09-06T05:01:35.228Z | wave_replanned |  | PREFLIGHT | reason=ACCEPTANCE_PROOF_REQUIRED remains the causal blocker. The subsequent idempotency-outcome audit confirmed no second wave, write lease, source mutation, or proof record was created by the blocked v1 replay. Use a new durable request identity and the already declared changed strategy: exact-byte adoption plus canonical agent_workflow verification, with zero intended byte changes. |
| 41263 | 2026-09-06T05:01:35.420Z | observation_span_recorded |  |  |  |
| 41264 | 2026-09-06T05:01:48.455Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41265 | 2026-09-06T05:01:48.603Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41266 | 2026-09-06T05:01:48.835Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41267 | 2026-09-06T05:01:49.036Z | state_transition | READY | ROUTED | reason=route_selected |
| 41268 | 2026-09-06T05:01:49.212Z | observation_span_recorded |  |  |  |
| 41269 | 2026-09-06T05:01:49.663Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0a6178ff1e3e49899a628318a5d75721 |
| 41270 | 2026-09-06T05:01:49.845Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41271 | 2026-09-06T05:01:50.241Z | existing_file_adoption_observed |  |  |  |
| 41272 | 2026-09-06T05:01:50.487Z | observation_span_recorded |  |  |  |
| 41273 | 2026-09-06T05:01:50.761Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0a6178ff1e3e49899a628318a5d75721 |
| 41274 | 2026-09-06T05:01:50.930Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41275 | 2026-09-06T05:01:51.303Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2aa67db646bc51dd; input_fingerprint=11ba20af0a4ec12439ab9a175f70519b88291b314604a47cbb97d0613cdd0d75 |
| 41276 | 2026-09-06T05:01:51.705Z | managed_process_admitted |  |  | owner=default |
| 41277 | 2026-09-06T05:01:52.013Z | managed_process_started |  |  | owner=default |
| 41278 | 2026-09-06T05:01:52.514Z | managed_process_terminal |  |  | owner=default |
| 41279 | 2026-09-06T05:01:52.847Z | proof_recorded |  |  | stage_id=check:2aa67db646bc51dd; status=passed; cache_hit=False; input_fingerprint=11ba20af0a4ec12439ab9a175f70519b88291b314604a47cbb97d0613cdd0d75 |
| 41280 | 2026-09-06T05:01:53.076Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3e0e407be2f242a3149c31cd9d47a6d92be261647d18d5abe5441459160c21ac |
| 41281 | 2026-09-06T05:01:53.440Z | managed_process_admitted |  |  | owner=default |
| 41282 | 2026-09-06T05:01:53.740Z | managed_process_started |  |  | owner=default |
| 41283 | 2026-09-06T05:02:35.965Z | managed_process_terminal |  |  | owner=default |
| 41284 | 2026-09-06T05:02:37.283Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3e0e407be2f242a3149c31cd9d47a6d92be261647d18d5abe5441459160c21ac |
| 41285 | 2026-09-06T05:02:37.564Z | observation_span_recorded |  |  |  |
| 41286 | 2026-09-06T05:02:37.746Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41928 | 2026-09-06T07:59:28.158Z | quality_outcome_recorded |  |  |  |
| 41929 | 2026-09-06T07:59:28.394Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41930 | 2026-09-06T07:59:28.697Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2aa67db646bc51dd | passed | 11ba20af0a4ec12439ab9a175f70519b88291b314604a47cbb97d0613cdd0d75 | False | 1164 | 0 |
| verify:tests | passed | 3e0e407be2f242a3149c31cd9d47a6d92be261647d18d5abe5441459160c21ac | False | 43781 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5e61468218f041d8b34d551870a0e95a | accepted | 58ee20d3a5b2607016b1880f4276437eb2dcf5df | 6906bfc42a02b4967ea0717a198af6c07a48dd36e297b29d9c44a53cc4cc6063 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `afeccf1272fba38cd714bef4a0903a407183d03d5b3825dd93a224decc0d9fe1`
