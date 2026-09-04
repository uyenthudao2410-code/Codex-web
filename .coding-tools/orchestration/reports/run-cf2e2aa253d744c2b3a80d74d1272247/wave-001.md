# Orchestration Wave 1

- Run: `cf2e2aa253d744c2b3a80d74d1272247`
- Wave: `a4fb60ed46d143d68949e528cf34c657`
- Objective: Preserve the current misplaced private runtime ledger from resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 into canonical root durable evidence before cleanup. Create a new non-overwriting recovery artifact .coding-tools/orchestration/recovered/misplaced-ledger-20260904-current.sqlite3, verify source and copy have identical SHA-256 and byte content, and make no other project changes. Do not remove the misplaced source yet. No commit/push yet.
- Objective revision: `1`
- Objective SHA-256: `b87c05457b91665f93656ab1ec17108af6371fed9fec9865815b918d21064da9`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `c0f826c94fd886a1b1012fe04fc121f2866d26653087f0a34fc8a7ce7c403899`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39313 | 2026-09-04T01:39:47.501Z | run_started |  | PREFLIGHT |  |
| 39314 | 2026-09-04T01:39:48.209Z | observation_span_recorded |  |  |  |
| 39315 | 2026-09-04T01:39:49.294Z | observation_span_recorded |  |  |  |
| 39316 | 2026-09-04T01:39:49.564Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 39317 | 2026-09-04T01:39:49.765Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 39318 | 2026-09-04T01:39:50.033Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39319 | 2026-09-04T01:39:50.241Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39320 | 2026-09-04T01:39:50.466Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 39321 | 2026-09-04T01:39:50.652Z | state_transition | READY | ROUTED | reason=route_selected |
| 39322 | 2026-09-04T01:39:50.845Z | observation_span_recorded |  |  |  |
| 39323 | 2026-09-04T01:39:53.014Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=df45c9aef7564618b0931e651a1dd9da |
| 39324 | 2026-09-04T01:39:53.443Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39325 | 2026-09-04T01:39:54.649Z | observation_span_recorded |  |  |  |
| 39326 | 2026-09-04T01:39:55.689Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=df45c9aef7564618b0931e651a1dd9da |
| 39327 | 2026-09-04T01:39:55.990Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39328 | 2026-09-04T01:39:57.311Z | proof_cache_miss |  |  | reason=cold; stage_id=check:087f5ad4161d6397; input_fingerprint=230f0f0b8a9dada5b9cb4b5c54771eb297a20b1e42625fecbcea2c7037f5f225 |
| 39329 | 2026-09-04T01:39:58.372Z | managed_process_admitted |  |  | owner=default |
| 39330 | 2026-09-04T01:39:58.844Z | managed_process_started |  |  | owner=default |
| 39331 | 2026-09-04T01:39:59.345Z | managed_process_terminal |  |  | owner=default |
| 39332 | 2026-09-04T01:39:59.819Z | proof_recorded |  |  | stage_id=check:087f5ad4161d6397; status=passed; cache_hit=False; input_fingerprint=230f0f0b8a9dada5b9cb4b5c54771eb297a20b1e42625fecbcea2c7037f5f225 |
| 39333 | 2026-09-04T01:40:00.181Z | proof_cache_miss |  |  | reason=cold; stage_id=check:be99502a2b696a17; input_fingerprint=5fb3c42bc9ab97f794c2ad3710d4e83cb93ce9f620091d08a376caee95b34adc |
| 39334 | 2026-09-04T01:40:00.818Z | managed_process_admitted |  |  | owner=default |
| 39335 | 2026-09-04T01:40:01.221Z | managed_process_started |  |  | owner=default |
| 39336 | 2026-09-04T01:40:01.781Z | managed_process_terminal |  |  | owner=default |
| 39337 | 2026-09-04T01:40:02.145Z | proof_recorded |  |  | stage_id=check:be99502a2b696a17; status=passed; cache_hit=False; input_fingerprint=5fb3c42bc9ab97f794c2ad3710d4e83cb93ce9f620091d08a376caee95b34adc |
| 39338 | 2026-09-04T01:40:02.460Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4a157278db95fb03; input_fingerprint=ef73e275924d44f4d89f560fed2c24091fa69cc122e2eba911aa1a3e39f28c7d |
| 39339 | 2026-09-04T01:40:02.978Z | managed_process_admitted |  |  | owner=default |
| 39340 | 2026-09-04T01:40:03.366Z | managed_process_started |  |  | owner=default |
| 39341 | 2026-09-04T01:40:03.967Z | managed_process_terminal |  |  | owner=default |
| 39342 | 2026-09-04T01:40:04.240Z | proof_recorded |  |  | stage_id=check:4a157278db95fb03; status=passed; cache_hit=False; input_fingerprint=ef73e275924d44f4d89f560fed2c24091fa69cc122e2eba911aa1a3e39f28c7d |
| 39343 | 2026-09-04T01:40:04.461Z | proof_cache_miss |  |  | reason=cold; stage_id=check:50ddda95d55a893a; input_fingerprint=d234f6043c9d37e95c1f4da0a80739176f28f2c477c535df961aeae02de70d6d |
| 39344 | 2026-09-04T01:40:04.834Z | managed_process_admitted |  |  | owner=default |
| 39345 | 2026-09-04T01:40:05.325Z | managed_process_started |  |  | owner=default |
| 39346 | 2026-09-04T01:40:06.535Z | managed_process_terminal |  |  | owner=default |
| 39347 | 2026-09-04T01:40:07.281Z | proof_recorded |  |  | stage_id=check:50ddda95d55a893a; status=passed; cache_hit=False; input_fingerprint=d234f6043c9d37e95c1f4da0a80739176f28f2c477c535df961aeae02de70d6d |
| 39348 | 2026-09-04T01:40:07.654Z | proof_cache_miss |  |  | reason=cold; stage_id=check:25ccdeb54c9eeea8; input_fingerprint=b7dc3a989e7dac70c7079685185b2c57aeab57cf11d6481fffb8a55f454f30d6 |
| 39349 | 2026-09-04T01:40:08.734Z | managed_process_admitted |  |  | owner=default |
| 39350 | 2026-09-04T01:40:09.438Z | managed_process_started |  |  | owner=default |
| 39351 | 2026-09-04T01:40:10.028Z | managed_process_terminal |  |  | owner=default |
| 39352 | 2026-09-04T01:40:10.104Z | proof_recorded |  |  | stage_id=check:25ccdeb54c9eeea8; status=passed; cache_hit=False; input_fingerprint=b7dc3a989e7dac70c7079685185b2c57aeab57cf11d6481fffb8a55f454f30d6 |
| 39353 | 2026-09-04T01:40:10.460Z | observation_span_recorded |  |  |  |
| 39354 | 2026-09-04T01:40:10.765Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 39355 | 2026-09-04T01:40:25.554Z | quality_outcome_recorded |  |  |  |
| 39356 | 2026-09-04T01:40:25.814Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 39357 | 2026-09-04T01:40:26.087Z | observation_span_recorded |  |  |  |
| 39358 | 2026-09-04T01:40:26.405Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:087f5ad4161d6397 | passed | 230f0f0b8a9dada5b9cb4b5c54771eb297a20b1e42625fecbcea2c7037f5f225 | False | 1735 | 0 |
| check:be99502a2b696a17 | passed | 5fb3c42bc9ab97f794c2ad3710d4e83cb93ce9f620091d08a376caee95b34adc | False | 1512 | 0 |
| check:4a157278db95fb03 | passed | ef73e275924d44f4d89f560fed2c24091fa69cc122e2eba911aa1a3e39f28c7d | False | 1277 | 0 |
| check:50ddda95d55a893a | passed | d234f6043c9d37e95c1f4da0a80739176f28f2c477c535df961aeae02de70d6d | False | 2421 | 0 |
| check:25ccdeb54c9eeea8 | passed | b7dc3a989e7dac70c7079685185b2c57aeab57cf11d6481fffb8a55f454f30d6 | False | 2145 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 31d0e8d9bf734292af158cde728e39bc | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 1abd70422eb9d0c59b3fd352ef7bf41ef0769ae97ff39de8513063924177a292 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `46`
- Chain head: `4b09599966086df9c31f20f76aa15ab8804dfa733bfdc4b1bb01b7a461e04647`
