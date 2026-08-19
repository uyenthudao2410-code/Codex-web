# Orchestration Wave 2

- Run: `482171d427dc4fdfb3c9b3e28cc42552`
- Wave: `8d9153fb9410486bb9370b6bf25cb85d`
- Objective: Implement token-accounting wave 2 only: canonical non-overlapping pricing; durable exact 7-day UsageEvent analytics across all runs with hourly UTC/by actor/provider/model/rolling 5m; strict conflicting usage_id rejection; provider economics excludes controller actor; expose analytics in control orchestration snapshot. Preserve accepted UsageEvent v2 and all unrelated work. No ChatWeb ingress/dashboard yet. No commit/push/restart.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `9d04e4178c88aa238673cfc54b302988f6b2622444f8f12311a54baff2245b08`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21070 | 2026-08-19T09:02:19.975Z | wave_replanned |  | PREFLIGHT | reason=Previous wave wrote no source and entered REPLAN because one orchestration_ledger.py patch hunk matched four locations. Changed strategy: split the ledger work into separately anchored method-level patches using exact function signatures and unique SQL/context; preserve the already recorded pre-first-write solution shadow; then run fresh compile/module-size/diff/tests only after source mutation. No stale proof reuse. |
| 21071 | 2026-08-19T09:02:21.006Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21072 | 2026-08-19T09:02:37.902Z | managed_process_admitted |  |  | owner=default |
| 21073 | 2026-08-19T09:02:38.156Z | managed_process_started |  |  | owner=default |
| 21074 | 2026-08-19T09:02:38.586Z | managed_process_terminal |  |  | owner=default |
| 21075 | 2026-08-19T09:03:10.871Z | managed_process_admitted |  |  | owner=default |
| 21076 | 2026-08-19T09:03:11.387Z | managed_process_started |  |  | owner=default |
| 21077 | 2026-08-19T09:03:12.621Z | managed_process_terminal |  |  | owner=default |
| 21078 | 2026-08-19T09:04:35.370Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21079 | 2026-08-19T09:04:35.587Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21080 | 2026-08-19T09:04:35.740Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21081 | 2026-08-19T09:04:35.937Z | state_transition | READY | ROUTED | reason=route_selected |
| 21082 | 2026-08-19T09:04:36.492Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=df2895beb5a24d1f86c128d583b8e6d0 |
| 21083 | 2026-08-19T09:04:36.636Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21084 | 2026-08-19T09:04:37.085Z | patch_surface_observed |  |  |  |
| 21085 | 2026-08-19T09:04:37.288Z | patch_surface_observed |  |  |  |
| 21086 | 2026-08-19T09:04:37.487Z | patch_surface_observed |  |  |  |
| 21087 | 2026-08-19T09:04:37.721Z | patch_surface_observed |  |  |  |
| 21088 | 2026-08-19T09:04:37.922Z | patch_surface_observed |  |  |  |
| 21089 | 2026-08-19T09:04:38.111Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=df2895beb5a24d1f86c128d583b8e6d0 |
| 21090 | 2026-08-19T09:04:38.326Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21091 | 2026-08-19T09:04:38.688Z | proof_cache_miss |  |  | reason=cold; stage_id=check:81ddaec2483a91e3; input_fingerprint=3cc129f830da0a732887cf50cc8fda1d268d222739e84a4d59587aceee22f34e |
| 21092 | 2026-08-19T09:04:39.100Z | managed_process_admitted |  |  | owner=default |
| 21093 | 2026-08-19T09:04:39.385Z | managed_process_started |  |  | owner=default |
| 21094 | 2026-08-19T09:04:39.972Z | managed_process_terminal |  |  | owner=default |
| 21095 | 2026-08-19T09:04:40.328Z | proof_recorded |  |  | stage_id=check:81ddaec2483a91e3; status=passed; cache_hit=False; input_fingerprint=3cc129f830da0a732887cf50cc8fda1d268d222739e84a4d59587aceee22f34e |
| 21096 | 2026-08-19T09:04:40.475Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=4ae8b6199e8b2d098d9139309b3f7e4741271b6a2ec947c7ee0ba404cc2c6043 |
| 21097 | 2026-08-19T09:04:40.808Z | managed_process_admitted |  |  | owner=default |
| 21098 | 2026-08-19T09:04:41.141Z | managed_process_started |  |  | owner=default |
| 21099 | 2026-08-19T09:04:41.614Z | managed_process_terminal |  |  | owner=default |
| 21100 | 2026-08-19T09:04:41.919Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=4ae8b6199e8b2d098d9139309b3f7e4741271b6a2ec947c7ee0ba404cc2c6043 |
| 21101 | 2026-08-19T09:04:42.120Z | proof_cache_miss |  |  | reason=cold; stage_id=check:75d548f3f8c894b5; input_fingerprint=e4f5d986a069fe2d45fd536ecb976098029723695751375128171f00b6389330 |
| 21102 | 2026-08-19T09:04:42.511Z | managed_process_admitted |  |  | owner=default |
| 21103 | 2026-08-19T09:04:42.867Z | managed_process_started |  |  | owner=default |
| 21104 | 2026-08-19T09:04:43.287Z | managed_process_terminal |  |  | owner=default |
| 21105 | 2026-08-19T09:04:43.594Z | proof_recorded |  |  | stage_id=check:75d548f3f8c894b5; status=passed; cache_hit=False; input_fingerprint=e4f5d986a069fe2d45fd536ecb976098029723695751375128171f00b6389330 |
| 21106 | 2026-08-19T09:04:43.810Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=c4f2a762613f90a9651f3e512090005fb4c30b7352e250eb8e7237e7e656dfe6 |
| 21107 | 2026-08-19T09:04:44.209Z | managed_process_admitted |  |  | owner=default |
| 21108 | 2026-08-19T09:04:44.487Z | managed_process_started |  |  | owner=default |
| 21109 | 2026-08-19T09:04:45.334Z | state_transition | PROVING | ABORTED | reason=Priority coordination stop before any new write in replacement wave 8d9153fb9410486bb9370b6bf25cb85d. Preserve the already-dirty token-accounting source from the prior replanned wave (usage_pricing.py, orchestration_ledger.py) and accepted usage_events.py exactly as-is. No transport/session isolation files are owned by this run. Resume this token objective after the legacy/unscoped cross-tab isolation fix is accepted and runtime-restarted. |
| 21110 | 2026-08-19T09:04:45.979Z | managed_process_terminal |  |  | owner=default |
| 21111 | 2026-08-19T09:04:46.130Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |
| 21112 | 2026-08-19T09:04:46.301Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=c4f2a762613f90a9651f3e512090005fb4c30b7352e250eb8e7237e7e656dfe6 |
| 21113 | 2026-08-19T09:04:47.078Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21114 | 2026-08-19T09:05:05.980Z | quality_outcome_recorded |  |  |  |
| 21115 | 2026-08-19T09:05:06.168Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21116 | 2026-08-19T09:05:06.525Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:81ddaec2483a91e3 | passed | 3cc129f830da0a732887cf50cc8fda1d268d222739e84a4d59587aceee22f34e | False | 1168 | 0 |
| check:80a1a46bd01d26a3 | passed | 4ae8b6199e8b2d098d9139309b3f7e4741271b6a2ec947c7ee0ba404cc2c6043 | False | 1125 | 0 |
| check:75d548f3f8c894b5 | passed | e4f5d986a069fe2d45fd536ecb976098029723695751375128171f00b6389330 | False | 1185 | 0 |
| verify:tests | passed | c4f2a762613f90a9651f3e512090005fb4c30b7352e250eb8e7237e7e656dfe6 | False | 1969 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 01003918da5a433cab8f7458f0ecef65 | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | d1f2dc1265121ea20619a8e4d83c9a12fec53760ffe663bbc976e0ec722a6db3 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `65`
- Chain head: `e9c5b9abd9c739f7042d273b2ccfe1baf4cf104b2042c4886645fecf71d6e28b`
