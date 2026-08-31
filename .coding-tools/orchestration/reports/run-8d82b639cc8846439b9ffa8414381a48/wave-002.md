# Orchestration Wave 2

- Run: `8d82b639cc8846439b9ffa8414381a48`
- Wave: `14a235d37900406783a6a9b4f0047832`
- Objective: Create a new EOCL-controlled source wave for E:\DEV\Codex-web to remove the idle AcceptedCodeActivationController auto-activation synchronous process-identity probe storm without weakening fail-closed activation authority. Current causal evidence: main HEAD a357e1bb45a68cfaf25b8a2aa99a133ab256102c with intentional dirty worktree; AUTO_ACTIVATION_INTERVAL_MS=3000; discover() calls ensureBaseline() before knowing whether accepted work exists; ensureBaseline() force-hashes recovery_host/coding_mcp/electron_ui and runtimeRevisionStatus(), where coding_mcp and electron_ui can trigger synchronous Windows process-identity probes; 120 cached recovery.ping samples show paired ~357-438 ms outliers every ~3 seconds; a 12-second read-only process census observed 34 powershell.exe children under current Recovery Host PID 29992; direct component hashing is only a few to low tens of milliseconds. Smallest causal solution: in electron/services/recoveryActionStore.js, after preserving forced Git/checkpoint discovery, if an established baseline exists and there is neither an active checkpoint nor an unprocessed accepted candidate, return before ensureBaseline(); still run ensureBaseline() when baseline is missing, an active checkpoint exists, or a candidate exists. Do not bypass preflight, revalidation, source-checkpoint authority, or exact activation checks. Add a focused regression in tests/accepted-code-activation.test.js proving the established-baseline/no-candidate idle path does not call disk/running revision providers while existing candidate/activation tests continue to protect the work-present path. Production behavior must remain unchanged until exact acceptance and a supported full-clean activation. Planned validation after mutation: node --test tests/accepted-code-activation.test.js tests/recovery-host.test.js tests/runtime-lifecycle.test.js; git diff --check -- electron/services/recoveryActionStore.js tests/accepted-code-activation.test.js. No commit, push, package, release, deploy, restart, raw HTTP, or mutation outside EOCL write authority.
- Objective revision: `2`
- Objective SHA-256: `90d42cf685ce50d8874b8f836d8846514d99c32bdc83adf28e267357f3abea78`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a357e1bb45a68cfaf25b8a2aa99a133ab256102c`
- Worktree fingerprint: `c29ee2bb310ac3d8ebaea221a9a69504b735cbcc6f54e95514e1891d4fac1b7c`
- Contract fingerprint: `e3ea0340218fa55274ddb092c5d1964a882a10a8c2bd6029c212d3623d581f45`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33328 | 2026-08-31T08:15:01.451Z | wave_replanned |  | PREFLIGHT | reason=Typed REPLAN after PATCH_CONTEXT_AMBIGUOUS: the source hunk now anchors the full async discover() method and the test hunk now anchors the unique adjacent full test names. Preserve the existing P4 shadow recommendation p0.6-auto-activation-idle-fast-path-v1 and transfer mutation authority only if the runtime can explicitly grant a Desktop/Codex local deep-single-lane lease for exactly the two requested files; otherwise fail closed without mutation. |
| 33329 | 2026-08-31T08:15:01.692Z | observation_span_recorded |  |  |  |
| 33330 | 2026-08-31T08:15:02.667Z | observation_span_recorded |  |  |  |
| 33331 | 2026-08-31T08:15:02.869Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 33332 | 2026-08-31T08:25:54.830Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=deep_single_lane; resolved=mcp_only |
| 33333 | 2026-08-31T08:25:55.026Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33334 | 2026-08-31T08:25:55.209Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33335 | 2026-08-31T08:25:55.383Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 33336 | 2026-08-31T08:25:55.559Z | state_transition | READY | ROUTED | reason=route_selected |
| 33337 | 2026-08-31T08:25:55.763Z | observation_span_recorded |  |  |  |
| 33338 | 2026-08-31T08:25:56.975Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=229c8e415fff4352886ec241f0d73ea8 |
| 33339 | 2026-08-31T08:25:57.166Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33340 | 2026-08-31T08:25:58.119Z | patch_surface_observed |  |  |  |
| 33341 | 2026-08-31T08:25:58.310Z | observation_span_recorded |  |  |  |
| 33342 | 2026-08-31T08:25:58.600Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=229c8e415fff4352886ec241f0d73ea8 |
| 33343 | 2026-08-31T08:25:58.756Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33344 | 2026-08-31T08:25:59.746Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7c4507e17de4a4fe; input_fingerprint=d13f5b68cd89ce7732293172b515d3089da38a26fd083fc10ae6ee107e738430 |
| 33345 | 2026-08-31T08:26:00.291Z | managed_process_admitted |  |  | owner=default |
| 33346 | 2026-08-31T08:26:00.604Z | managed_process_started |  |  | owner=default |
| 33347 | 2026-08-31T08:26:46.747Z | managed_process_terminal |  |  | owner=default |
| 33348 | 2026-08-31T08:26:47.115Z | proof_recorded |  |  | stage_id=check:7c4507e17de4a4fe; status=passed; cache_hit=False; input_fingerprint=d13f5b68cd89ce7732293172b515d3089da38a26fd083fc10ae6ee107e738430 |
| 33349 | 2026-08-31T08:26:47.360Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a66b2f6b14d25aac; input_fingerprint=d36615eb59121cfd1f499ac35a60392284a114e06f55a8d66d8bfe15bd227e66 |
| 33350 | 2026-08-31T08:26:47.818Z | managed_process_admitted |  |  | owner=default |
| 33351 | 2026-08-31T08:26:48.148Z | managed_process_started |  |  | owner=default |
| 33352 | 2026-08-31T08:26:48.588Z | managed_process_terminal |  |  | owner=default |
| 33353 | 2026-08-31T08:26:48.908Z | proof_recorded |  |  | stage_id=check:a66b2f6b14d25aac; status=passed; cache_hit=False; input_fingerprint=d36615eb59121cfd1f499ac35a60392284a114e06f55a8d66d8bfe15bd227e66 |
| 33354 | 2026-08-31T08:26:49.841Z | observation_span_recorded |  |  |  |
| 33355 | 2026-08-31T08:26:50.058Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 33356 | 2026-08-31T08:29:08.580Z | quality_outcome_recorded |  |  |  |
| 33357 | 2026-08-31T08:29:08.763Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 33358 | 2026-08-31T08:29:09.056Z | observation_span_recorded |  |  |  |
| 33359 | 2026-08-31T08:29:09.272Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7c4507e17de4a4fe | passed | d13f5b68cd89ce7732293172b515d3089da38a26fd083fc10ae6ee107e738430 | False | 46915 | 0 |
| check:a66b2f6b14d25aac | passed | d36615eb59121cfd1f499ac35a60392284a114e06f55a8d66d8bfe15bd227e66 | False | 1144 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5b58d2aa9ce544939362fc33eb0cd141 | accepted | a357e1bb45a68cfaf25b8a2aa99a133ab256102c | 8e666fe0d5ef59d0094c6a28bd4297dc73a967f98367c1c347a7df908014c444 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `034069a93b53a56a52238e574a738ef72294ce41331de7231e777e876e52877c`
