# Orchestration Wave 1

- Run: `53ac6845facd4cbc94154f712b6bbf27`
- Wave: `8580fda5cf1b4ff7a063261f39d42691`
- Objective: Canonicalize and accept the already-present activation/recovery/connector hotfix in the authoritative worktree so Recovery Host can produce a fresh durable accepted-code closure checkpoint for controlled restart canary. Preserve all unrelated dirty work. Scope only: electron/services/activationEpoch.js; electron/services/fullCleanActivation.js; electron/services/recoveryHost.js; resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py; resources/coding-tools-mcp/coding_tools_mcp/http_hub_identity.py; tests/activation-self-recovery.test.js; resources/coding-tools-mcp/tests/test_activation_restart_escape.py; resources/coding-tools-mcp/tests/test_connector_bootstrap_identity.py. Inspect the current scoped diff against HEAD b64c43c7e092301dd9abdfad32d4dc1910192485, verify it matches the proven causal fixes: durable expiry via FullCleanActivation boundary, confirmed restart escape through closed startup admission only, preserved connector-pending Tunnel recovery, and ChatWeb identity fallback for explicit chatweb client id with missing type. Do not rewrite or clean unrelated paths. Define the smallest focused proof required to bind an accepted-code checkpoint before restart canary.
- Objective revision: `1`
- Objective SHA-256: `0ebc67bdd6fd693e26862b1ff07d3c2ad306536c3a250b42fdc253dd3bc962e6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `b64c43c7e092301dd9abdfad32d4dc1910192485`
- Worktree fingerprint: `c9cfd4f9a043e50249fbf998e36e0c0870741c94a0c06d435e24427b058dca8a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 31271 | 2026-08-27T19:36:10.129Z | run_started |  | PREFLIGHT |  |
| 31272 | 2026-08-27T19:36:10.338Z | observation_span_recorded |  |  |  |
| 31273 | 2026-08-27T19:36:10.477Z | solution_shadow_recommended |  |  |  |
| 31274 | 2026-08-27T19:36:11.905Z | observation_span_recorded |  |  |  |
| 31275 | 2026-08-27T19:36:12.010Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 31276 | 2026-08-27T19:37:38.767Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 31277 | 2026-08-27T19:37:38.899Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 31278 | 2026-08-27T19:37:39.004Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 31279 | 2026-08-27T19:37:39.120Z | state_transition | READY | ROUTED | reason=route_selected |
| 31280 | 2026-08-27T19:37:39.251Z | observation_span_recorded |  |  |  |
| 31281 | 2026-08-27T19:37:40.074Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ab3d551ce35c46028bdf40f6674fe988 |
| 31282 | 2026-08-27T19:37:40.183Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 31283 | 2026-08-27T19:37:41.056Z | observation_span_recorded |  |  |  |
| 31284 | 2026-08-27T19:37:41.256Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ab3d551ce35c46028bdf40f6674fe988 |
| 31285 | 2026-08-27T19:37:41.365Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 31286 | 2026-08-27T19:37:42.117Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:619ebb36c1e3cab1; input_fingerprint=feee71284ab41e35d4adeedfcaa15a980ea6fd2c43fa9f38a973142bac5c50a9 |
| 31287 | 2026-08-27T19:37:42.357Z | managed_process_admitted |  |  | owner=default |
| 31288 | 2026-08-27T19:37:42.538Z | managed_process_started |  |  | owner=default |
| 31289 | 2026-08-27T19:37:42.884Z | managed_process_terminal |  |  | owner=default |
| 31290 | 2026-08-27T19:37:43.099Z | proof_recorded |  |  | stage_id=check:619ebb36c1e3cab1; status=passed; cache_hit=False; input_fingerprint=feee71284ab41e35d4adeedfcaa15a980ea6fd2c43fa9f38a973142bac5c50a9 |
| 31291 | 2026-08-27T19:37:43.184Z | proof_cache_miss |  |  | reason=cold; stage_id=check:90732f36c651cb3c; input_fingerprint=e539c13d8b540b6ff6c8ccf44c55b9c6105bf6b41e22763e2f2eef9424bf0d0c |
| 31292 | 2026-08-27T19:37:43.447Z | managed_process_admitted |  |  | owner=default |
| 31293 | 2026-08-27T19:37:43.674Z | managed_process_started |  |  | owner=default |
| 31294 | 2026-08-27T19:37:44.006Z | managed_process_terminal |  |  | owner=default |
| 31295 | 2026-08-27T19:37:44.273Z | proof_recorded |  |  | stage_id=check:90732f36c651cb3c; status=passed; cache_hit=False; input_fingerprint=e539c13d8b540b6ff6c8ccf44c55b9c6105bf6b41e22763e2f2eef9424bf0d0c |
| 31296 | 2026-08-27T19:37:44.374Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8be7cde4d81ebb48; input_fingerprint=1ab14a6b435e103182281ea2e8be0c7825861b0a04b272bb026490e5103cc335 |
| 31297 | 2026-08-27T19:37:44.584Z | managed_process_admitted |  |  | owner=default |
| 31298 | 2026-08-27T19:37:44.784Z | managed_process_started |  |  | owner=default |
| 31299 | 2026-08-27T19:37:45.186Z | managed_process_terminal |  |  | owner=default |
| 31300 | 2026-08-27T19:37:45.434Z | proof_recorded |  |  | stage_id=check:8be7cde4d81ebb48; status=passed; cache_hit=False; input_fingerprint=1ab14a6b435e103182281ea2e8be0c7825861b0a04b272bb026490e5103cc335 |
| 31301 | 2026-08-27T19:37:45.548Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9cb288f22bf3a8c4; input_fingerprint=c92de77ff8973c1d90cb7f79188072eb3a54ae67164211678bb73dfa5538d10f |
| 31302 | 2026-08-27T19:37:45.799Z | managed_process_admitted |  |  | owner=default |
| 31303 | 2026-08-27T19:37:45.999Z | managed_process_started |  |  | owner=default |
| 31304 | 2026-08-27T19:37:49.683Z | managed_process_terminal |  |  | owner=default |
| 31305 | 2026-08-27T19:37:49.892Z | proof_recorded |  |  | stage_id=check:9cb288f22bf3a8c4; status=passed; cache_hit=False; input_fingerprint=c92de77ff8973c1d90cb7f79188072eb3a54ae67164211678bb73dfa5538d10f |
| 31306 | 2026-08-27T19:37:49.986Z | proof_cache_miss |  |  | reason=cold; stage_id=check:80e034a8cfa0d216; input_fingerprint=b7396af33f8c1c28ba51716c023b8ac214465b07b1ac73d80ca48217dbb04394 |
| 31307 | 2026-08-27T19:37:50.223Z | managed_process_admitted |  |  | owner=default |
| 31308 | 2026-08-27T19:37:50.448Z | managed_process_started |  |  | owner=default |
| 31309 | 2026-08-27T19:37:53.090Z | managed_process_terminal |  |  | owner=default |
| 31310 | 2026-08-27T19:37:53.340Z | proof_recorded |  |  | stage_id=check:80e034a8cfa0d216; status=passed; cache_hit=False; input_fingerprint=b7396af33f8c1c28ba51716c023b8ac214465b07b1ac73d80ca48217dbb04394 |
| 31311 | 2026-08-27T19:37:53.458Z | proof_cache_miss |  |  | reason=cold; stage_id=check:73a6f8cf7686c9c2; input_fingerprint=da2d3baf7a47e3926ab1a18be9b8209602399bae45ed248477557630dcdc674b |
| 31312 | 2026-08-27T19:37:53.750Z | managed_process_admitted |  |  | owner=default |
| 31313 | 2026-08-27T19:37:53.957Z | managed_process_started |  |  | owner=default |
| 31314 | 2026-08-27T19:37:54.315Z | managed_process_terminal |  |  | owner=default |
| 31315 | 2026-08-27T19:37:54.532Z | proof_recorded |  |  | stage_id=check:73a6f8cf7686c9c2; status=passed; cache_hit=False; input_fingerprint=da2d3baf7a47e3926ab1a18be9b8209602399bae45ed248477557630dcdc674b |
| 31316 | 2026-08-27T19:37:54.649Z | observation_span_recorded |  |  |  |
| 31317 | 2026-08-27T19:37:54.760Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 31318 | 2026-08-27T19:38:20.200Z | quality_outcome_recorded |  |  |  |
| 31319 | 2026-08-27T19:38:20.309Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 31320 | 2026-08-27T19:38:20.433Z | observation_span_recorded |  |  |  |
| 31321 | 2026-08-27T19:38:20.558Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:619ebb36c1e3cab1 | passed | feee71284ab41e35d4adeedfcaa15a980ea6fd2c43fa9f38a973142bac5c50a9 | False | 741 | 0 |
| check:90732f36c651cb3c | passed | e539c13d8b540b6ff6c8ccf44c55b9c6105bf6b41e22763e2f2eef9424bf0d0c | False | 815 | 0 |
| check:8be7cde4d81ebb48 | passed | 1ab14a6b435e103182281ea2e8be0c7825861b0a04b272bb026490e5103cc335 | False | 818 | 0 |
| check:9cb288f22bf3a8c4 | passed | c92de77ff8973c1d90cb7f79188072eb3a54ae67164211678bb73dfa5538d10f | False | 4100 | 0 |
| check:80e034a8cfa0d216 | passed | b7396af33f8c1c28ba51716c023b8ac214465b07b1ac73d80ca48217dbb04394 | False | 3106 | 0 |
| check:73a6f8cf7686c9c2 | passed | da2d3baf7a47e3926ab1a18be9b8209602399bae45ed248477557630dcdc674b | False | 869 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1d045051f7a949a392b06563e62c9438 | accepted | b64c43c7e092301dd9abdfad32d4dc1910192485 | b3232ed4d201fb20da4376df5343deae649e161186276816c41e776df48efb8e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `a2e65dc7098db8e2a155572fff3b88018d88f1a1d376cc7a188aeab2c417313a`
