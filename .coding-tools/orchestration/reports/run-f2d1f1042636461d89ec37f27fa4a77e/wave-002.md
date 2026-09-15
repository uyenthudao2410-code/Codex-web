# Orchestration Wave 2

- Run: `f2d1f1042636461d89ec37f27fa4a77e`
- Wave: `4c4c35561b3849ada137b709bb7d32e5`
- Objective: Fix the live local continuation approval defect for Problem prl-e918c7d33e70c2d304d0797e11b05fcb revision 2: local loopback HTTP finalization must revalidate the exact attested controller identity frozen into the challenge, not re-derive controller identity from the loopback request context. Preserve generation, owner, endpoint, controller-lease fencing and fail closed on drift. Add regression coverage for the real finalization path. Preserve unrelated dirty work.
- Objective revision: `2`
- Objective SHA-256: `43a91ef828849a40812d06651a75376c9d8618c9b6e2f3004dfcf023d41ca262`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `712d72c1e86fcdf3e1c26d0714dcdcb315341bc3cb4737b8824afa44dd8e70b8`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 56306 | 2026-09-15T05:14:46.259Z | wave_replanned |  | PREFLIGHT | reason=The previous prepared wave entered REPLAN because volatile runtime/evidence updates changed the worktree fingerprint after preflight. The causal source target, Problem revision, controller-fence diagnosis, and two-file repair scope are unchanged; refresh the wave without adopting or overwriting unrelated dirty work. |
| 56307 | 2026-09-15T05:14:46.646Z | observation_span_recorded |  |  |  |
| 56308 | 2026-09-15T05:14:52.085Z | observation_span_recorded |  |  |  |
| 56309 | 2026-09-15T05:14:52.397Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 56310 | 2026-09-15T05:15:11.009Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 56311 | 2026-09-15T05:15:11.249Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 56312 | 2026-09-15T05:15:11.473Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 56313 | 2026-09-15T05:15:11.651Z | state_transition | READY | ROUTED | reason=route_selected |
| 56314 | 2026-09-15T05:15:11.907Z | observation_span_recorded |  |  |  |
| 56315 | 2026-09-15T05:15:12.427Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=12e39ac21cfc4ea29582d6fab0cd4175 |
| 56316 | 2026-09-15T05:15:12.660Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 56317 | 2026-09-15T05:15:13.184Z | patch_surface_observed |  |  |  |
| 56318 | 2026-09-15T05:15:13.457Z | observation_span_recorded |  |  |  |
| 56319 | 2026-09-15T05:15:13.861Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=12e39ac21cfc4ea29582d6fab0cd4175 |
| 56320 | 2026-09-15T05:15:14.084Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 56321 | 2026-09-15T05:15:14.551Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a4bd26a9f5111a229219708f9adc151681f21500b23ad44536e420d579d5e012 |
| 56322 | 2026-09-15T05:15:14.969Z | managed_process_admitted |  |  | owner=default |
| 56323 | 2026-09-15T05:15:15.397Z | managed_process_started |  |  | owner=default |
| 56324 | 2026-09-15T05:15:19.064Z | managed_process_terminal |  |  | owner=default |
| 56325 | 2026-09-15T05:15:20.634Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a4bd26a9f5111a229219708f9adc151681f21500b23ad44536e420d579d5e012 |
| 56326 | 2026-09-15T05:15:21.458Z | observation_span_recorded |  |  |  |
| 56327 | 2026-09-15T05:15:21.656Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 56328 | 2026-09-15T05:15:21.874Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 56329 | 2026-09-15T05:16:05.734Z | managed_process_admitted |  |  | owner=default |
| 56330 | 2026-09-15T05:16:06.108Z | managed_process_started |  |  | owner=default |
| 56331 | 2026-09-15T05:16:06.824Z | managed_process_terminal |  |  | owner=default |
| 56332 | 2026-09-15T05:16:14.496Z | managed_process_admitted |  |  | owner=default |
| 56333 | 2026-09-15T05:16:14.851Z | managed_process_started |  |  | owner=default |
| 56334 | 2026-09-15T05:16:15.374Z | managed_process_terminal |  |  | owner=default |
| 56335 | 2026-09-15T05:16:23.468Z | managed_process_admitted |  |  | owner=default |
| 56336 | 2026-09-15T05:16:23.866Z | managed_process_started |  |  | owner=default |
| 56337 | 2026-09-15T05:16:24.466Z | managed_process_terminal |  |  | owner=default |
| 56338 | 2026-09-15T05:16:32.799Z | managed_process_admitted |  |  | owner=default |
| 56339 | 2026-09-15T05:16:33.166Z | managed_process_started |  |  | owner=default |
| 56340 | 2026-09-15T05:16:33.838Z | managed_process_terminal |  |  | owner=default |
| 56341 | 2026-09-15T05:16:46.498Z | managed_process_admitted |  |  | owner=default |
| 56342 | 2026-09-15T05:16:46.885Z | managed_process_started |  |  | owner=default |
| 56343 | 2026-09-15T05:16:47.436Z | managed_process_terminal |  |  | owner=default |
| 56344 | 2026-09-15T05:16:54.237Z | managed_process_admitted |  |  | owner=default |
| 56345 | 2026-09-15T05:16:54.578Z | managed_process_started |  |  | owner=default |
| 56346 | 2026-09-15T05:16:55.255Z | managed_process_terminal |  |  | owner=default |
| 56347 | 2026-09-15T05:17:02.120Z | managed_process_admitted |  |  | owner=default |
| 56348 | 2026-09-15T05:17:02.538Z | managed_process_started |  |  | owner=default |
| 56349 | 2026-09-15T05:17:03.212Z | managed_process_terminal |  |  | owner=default |
| 56350 | 2026-09-15T05:17:09.632Z | managed_process_admitted |  |  | owner=default |
| 56351 | 2026-09-15T05:17:10.044Z | managed_process_started |  |  | owner=default |
| 56352 | 2026-09-15T05:17:10.661Z | managed_process_terminal |  |  | owner=default |
| 56353 | 2026-09-15T05:17:19.035Z | managed_process_admitted |  |  | owner=default |
| 56354 | 2026-09-15T05:17:19.380Z | managed_process_started |  |  | owner=default |
| 56355 | 2026-09-15T05:17:19.953Z | managed_process_terminal |  |  | owner=default |
| 56356 | 2026-09-15T05:17:26.447Z | managed_process_admitted |  |  | owner=default |
| 56357 | 2026-09-15T05:17:26.795Z | managed_process_started |  |  | owner=default |
| 56358 | 2026-09-15T05:17:27.361Z | managed_process_terminal |  |  | owner=default |
| 56359 | 2026-09-15T05:17:34.646Z | managed_process_admitted |  |  | owner=default |
| 56360 | 2026-09-15T05:17:35.080Z | managed_process_started |  |  | owner=default |
| 56361 | 2026-09-15T05:17:35.696Z | managed_process_terminal |  |  | owner=default |
| 56362 | 2026-09-15T05:17:44.029Z | managed_process_admitted |  |  | owner=default |
| 56363 | 2026-09-15T05:17:44.346Z | managed_process_started |  |  | owner=default |
| 56364 | 2026-09-15T05:17:44.963Z | managed_process_terminal |  |  | owner=default |
| 56365 | 2026-09-15T05:17:57.151Z | quality_outcome_recorded |  |  |  |
| 56366 | 2026-09-15T05:17:57.396Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 56367 | 2026-09-15T05:17:57.762Z | observation_span_recorded |  |  |  |
| 56368 | 2026-09-15T05:17:57.998Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 56369 | 2026-09-15T05:17:58.243Z | observation_span_recorded |  |  |  |
| 56370 | 2026-09-15T05:17:58.495Z | observation_span_recorded |  |  |  |
| 56371 | 2026-09-15T05:17:58.813Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | a4bd26a9f5111a229219708f9adc151681f21500b23ad44536e420d579d5e012 | False | 5656 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 620f3a480de54e7d9d1bcd572d576a84 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 1662ab1090bde691cd025f4aa76c15817ecff5f4cf2940c823255a1c7071beef | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `74`
- Chain head: `b962efafea5336339680526c32cfa374f77ca32a1192190e79a10f239a9e79f5`
