# Orchestration Wave 2

- Run: `655e0aa366fe4815997bfd84d8f525e0`
- Wave: `af1f4a879a7b424589d692a250652bf8`
- Objective: Fix only the two known research-stress fixture defects G04_cross_source_stable_signal_recovers and S01_rare_positive_strong_signal_recovers. Do not change canonical validator semantics, readiness thresholds, promotion policy, P5 treatment behavior, or synthetic promotion rules. Preserve the v5 validator behavior that already makes G03/M01/T02 pass. Acceptance: raw run_p4_research_stress_suite.py must become 35/35 PASS with blind_spots=[], multilayer strict must remain 37/37 PASS with canonical non-interference, and canonical readiness before/after the benchmark must remain unchanged. Do not commit, push, restart, or activate treatment in this wave.
- Mode: `mcp_only`
- Base HEAD: `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2`
- Worktree fingerprint: `bff87f50212761e9dda8b9aade4abda8b951ab58f797f6578926fc494283d120`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 22545 | 2026-08-20T04:30:49.494Z | wave_replanned |  | PREFLIGHT | reason=First fixture wave proved G04 is fixed (canonical valid with 4/4 source folds and min gain 0.25), but S01 still failed because the deterministic 17-mod-100 positive sequence produced rolling windows with varying rare-positive prevalence. Change only S01 fixture outcome spacing to stable 4-of-10 high-risk opportunities; do not change validator logic. |
| 22546 | 2026-08-20T04:30:49.664Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 22547 | 2026-08-20T04:30:49.829Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 22548 | 2026-08-20T04:30:49.988Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 22549 | 2026-08-20T04:30:50.129Z | state_transition | READY | ROUTED | reason=route_selected |
| 22550 | 2026-08-20T04:30:50.574Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=38254a6d857549a491af8c2330ba04bc |
| 22551 | 2026-08-20T04:30:50.714Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 22552 | 2026-08-20T04:30:51.104Z | patch_surface_observed |  |  |  |
| 22553 | 2026-08-20T04:30:51.333Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=38254a6d857549a491af8c2330ba04bc |
| 22554 | 2026-08-20T04:30:51.504Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 22555 | 2026-08-20T04:30:51.864Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:3045ec66daf3a081; input_fingerprint=b47ef9b5ed3cbfd5d9dc1d8905c10e94ce79c8335d4dd0d6cb990e4c907e64d0 |
| 22556 | 2026-08-20T04:30:52.194Z | managed_process_admitted |  |  | owner=default |
| 22557 | 2026-08-20T04:30:52.511Z | managed_process_started |  |  | owner=default |
| 22558 | 2026-08-20T04:30:52.954Z | managed_process_terminal |  |  | owner=default |
| 22559 | 2026-08-20T04:30:53.280Z | proof_recorded |  |  | stage_id=check:3045ec66daf3a081; status=passed; cache_hit=False; input_fingerprint=b47ef9b5ed3cbfd5d9dc1d8905c10e94ce79c8335d4dd0d6cb990e4c907e64d0 |
| 22560 | 2026-08-20T04:30:53.507Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fd71cdc4b22e7c92; input_fingerprint=ac7d3558428510a73678294d276c1f681cb48052792c714c1b32cf22c8810155 |
| 22561 | 2026-08-20T04:30:53.886Z | managed_process_admitted |  |  | owner=default |
| 22562 | 2026-08-20T04:30:54.213Z | managed_process_started |  |  | owner=default |
| 22563 | 2026-08-20T04:31:21.928Z | managed_process_terminal |  |  | owner=default |
| 22564 | 2026-08-20T04:31:22.239Z | proof_recorded |  |  | stage_id=check:fd71cdc4b22e7c92; status=passed; cache_hit=False; input_fingerprint=ac7d3558428510a73678294d276c1f681cb48052792c714c1b32cf22c8810155 |
| 22565 | 2026-08-20T04:31:22.457Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9647a5d1f13b481d; input_fingerprint=4387d4fdb39ecfa15741071eff7933f9db7d4f59c0ad24c1950966b87aff43ff |
| 22566 | 2026-08-20T04:31:22.807Z | managed_process_admitted |  |  | owner=default |
| 22567 | 2026-08-20T04:31:23.061Z | managed_process_started |  |  | owner=default |
| 22568 | 2026-08-20T04:31:58.424Z | managed_process_terminal |  |  | owner=default |
| 22569 | 2026-08-20T04:31:58.757Z | proof_recorded |  |  | stage_id=check:9647a5d1f13b481d; status=passed; cache_hit=False; input_fingerprint=4387d4fdb39ecfa15741071eff7933f9db7d4f59c0ad24c1950966b87aff43ff |
| 22570 | 2026-08-20T04:31:58.963Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e1ab31e9dd9881d2; input_fingerprint=eb660f2f70f9ef7dce5fea7489e5c6ce580b7faa536dd8ce745cd7ec8aca54e1 |
| 22571 | 2026-08-20T04:31:59.342Z | managed_process_admitted |  |  | owner=default |
| 22572 | 2026-08-20T04:31:59.662Z | managed_process_started |  |  | owner=default |
| 22573 | 2026-08-20T04:32:00.145Z | managed_process_terminal |  |  | owner=default |
| 22574 | 2026-08-20T04:32:00.491Z | proof_recorded |  |  | stage_id=check:e1ab31e9dd9881d2; status=passed; cache_hit=False; input_fingerprint=eb660f2f70f9ef7dce5fea7489e5c6ce580b7faa536dd8ce745cd7ec8aca54e1 |
| 22575 | 2026-08-20T04:32:00.724Z | proof_cache_miss |  |  | reason=cold; stage_id=check:22fd1133c1971a6e; input_fingerprint=6ead82ad7b54c930d39af2c4b93a3c4a660b04f34e4397bc40183fedf4e926a6 |
| 22576 | 2026-08-20T04:32:01.052Z | managed_process_admitted |  |  | owner=default |
| 22577 | 2026-08-20T04:32:01.341Z | managed_process_started |  |  | owner=default |
| 22578 | 2026-08-20T04:32:01.780Z | managed_process_terminal |  |  | owner=default |
| 22579 | 2026-08-20T04:32:02.178Z | proof_recorded |  |  | stage_id=check:22fd1133c1971a6e; status=passed; cache_hit=False; input_fingerprint=6ead82ad7b54c930d39af2c4b93a3c4a660b04f34e4397bc40183fedf4e926a6 |
| 22580 | 2026-08-20T04:32:02.641Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 22581 | 2026-08-20T04:32:50.974Z | quality_outcome_recorded |  |  |  |
| 22582 | 2026-08-20T04:32:51.145Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 22583 | 2026-08-20T04:32:51.486Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3045ec66daf3a081 | passed | b47ef9b5ed3cbfd5d9dc1d8905c10e94ce79c8335d4dd0d6cb990e4c907e64d0 | False | 1078 | 0 |
| check:fd71cdc4b22e7c92 | passed | ac7d3558428510a73678294d276c1f681cb48052792c714c1b32cf22c8810155 | False | 28384 | 0 |
| check:9647a5d1f13b481d | passed | 4387d4fdb39ecfa15741071eff7933f9db7d4f59c0ad24c1950966b87aff43ff | False | 35978 | 0 |
| check:e1ab31e9dd9881d2 | passed | eb660f2f70f9ef7dce5fea7489e5c6ce580b7faa536dd8ce745cd7ec8aca54e1 | False | 1218 | 0 |
| check:22fd1133c1971a6e | passed | 6ead82ad7b54c930d39af2c4b93a3c4a660b04f34e4397bc40183fedf4e926a6 | False | 1103 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bae4a87f663b4371a18229ad405c9c90 | accepted | 4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2 | 0eaee50f50dfe772eaf9824e62da7493f814eabae2ecaee5ee28c559acf6c087 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `261defdf25750d0535920a99325b36111e5b3a30c65d20ff950f86e6b7dd7a6e`
