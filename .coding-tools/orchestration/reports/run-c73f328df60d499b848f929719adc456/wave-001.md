# Orchestration Wave 1

- Run: `c73f328df60d499b848f929719adc456`
- Wave: `5238ff8b0f0345659eaee364f63ae65d`
- Objective: Deep deterministic evaluation of Tools-Codex-web performance, efficiency, and cost without paid provider calls. Locate existing benchmark/economics/profiling scripts, accepted-result economics projections, proof/cache/idempotency telemetry, and representative test harnesses. Do not modify files and do not dispatch external review or candidate models.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `5b5a8348123ea5392e9febb11df9618fc5406527725a189a1135cf9c0c5f8428`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| opencode-4adddedf49c4c36b045636c73b96707bda4f1518 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-ca3f1badbe696785d921b42c1bdcc8ed5d39e44b | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-a4366e741423471c62ec9b32a397d87ec4e2b49a | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-fdf7930009125c23e1411e36c282213380b48ad5 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-79ee72b30e2201002a9252d1cdf31b104ac3b652 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-b49e7a6d8157b2ea5bd0fecf230be434a0a7f8df | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-6e07ec217198fe25a3a66c48a5770d635848eaff | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-37fe4c1e294436d2fca80ae12ac6f67544bfe7d9 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-a5358204498fb405016e0dbecc8a216a553ea073 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-63cd63870087112bd7f9e542375b0abd0311afd0 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-151abfe44dfb36238223f707bac4f1c32952d77d | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-81706888f2395ff0470f2bee40a4c779248be8d7 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-3154692aea51b56878b0f5e5ed6889d5a95a6f37 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-9f4008f1c05a28c816ad0ae62be068a054542f3e | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-b5051f5afb6810d506af00e77be7c1568ce9b600 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-deec6a0e2f36aee3028dd11523fd46e56e483bde | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-dd92147e55a55d7cc3b3990c0f026357d0518e10 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-5d5b2e03ba29883834f71955a1e5af3f42557952 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-3e71b3f02794c8a74b1c13f5f60f2ac6013f92d0 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-8396a73142c5deb095a87c35f810c93655c098d6 | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-a506338f92ac5cc533db34eeab2e5835c28d0a5c | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |
| opencode-e40615f719aec3c5f029c244a81b01c5bc81d73a | opencode | opencode | opencode-go/deepseek-v4-pro | opencode-go/deepseek-v4-pro |  | completed |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4273 | 2026-08-15T04:52:07.947Z | run_started |  | PREFLIGHT |  |
| 4274 | 2026-08-15T04:52:08.122Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4275 | 2026-08-15T04:52:08.294Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4276 | 2026-08-15T04:52:08.503Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4277 | 2026-08-15T04:52:08.727Z | state_transition | READY | ROUTED | reason=route_selected |
| 4278 | 2026-08-15T04:52:09.417Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=44499779ea8647979e4298fa150e7bf1 |
| 4279 | 2026-08-15T04:52:09.551Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4280 | 2026-08-15T04:52:09.851Z | external_delegation_started | EXECUTING | EXECUTING | status=active |
| 4281 | 2026-08-15T04:52:10.428Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=44499779ea8647979e4298fa150e7bf1 |
| 4282 | 2026-08-15T04:52:10.631Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4283 | 2026-08-15T04:52:10.926Z | external_delegation_finished | EXECUTING | EXECUTING | status=completed |
| 4284 | 2026-08-15T04:52:11.271Z | usage_event |  |  | status=completed |
| 4285 | 2026-08-15T04:52:11.264Z | external_delegation_started | PROVING | PROVING | status=active |
| 4286 | 2026-08-15T04:52:11.269Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6f4f79c194f7b79a; input_fingerprint=1fcbbbc59f0763961c197826e9669defc1c82d02f36b2b25a43b25b0bc6e0856 |
| 4287 | 2026-08-15T04:52:12.128Z | proof_recorded |  |  | stage_id=check:6f4f79c194f7b79a; status=passed; cache_hit=False; input_fingerprint=1fcbbbc59f0763961c197826e9669defc1c82d02f36b2b25a43b25b0bc6e0856 |
| 4288 | 2026-08-15T04:52:12.341Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0df7eea678679411e29fb3c229075ef6e68f0d3e7643a48aecac3e0706e78b9e |
| 4289 | 2026-08-15T04:52:12.789Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0df7eea678679411e29fb3c229075ef6e68f0d3e7643a48aecac3e0706e78b9e |
| 4290 | 2026-08-15T04:52:12.991Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4291 | 2026-08-15T04:52:19.984Z | external_delegation_updated | ACCEPTING | ACCEPTING | status=active |
| 4292 | 2026-08-15T04:52:20.813Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4293 | 2026-08-15T04:52:21.014Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4294 | 2026-08-15T04:52:21.492Z | usage_event |  |  | status=completed |
| 4295 | 2026-08-15T04:52:26.449Z | external_delegation_updated | ACCEPTING | ACCEPTING | status=active |
| 4296 | 2026-08-15T04:52:27.290Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4297 | 2026-08-15T04:52:27.431Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4298 | 2026-08-15T04:52:27.812Z | usage_event |  |  | status=completed |
| 4299 | 2026-08-15T04:52:33.963Z | external_delegation_updated | ACCEPTING | ACCEPTING | status=active |
| 4300 | 2026-08-15T04:52:34.637Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4301 | 2026-08-15T04:52:34.801Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4302 | 2026-08-15T04:52:35.267Z | usage_event |  |  | status=completed |
| 4303 | 2026-08-15T04:52:40.849Z | external_delegation_updated | ACCEPTING | ACCEPTING | status=active |
| 4304 | 2026-08-15T04:52:41.916Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4305 | 2026-08-15T04:52:42.196Z | usage_event |  |  | status=completed |
| 4306 | 2026-08-15T04:52:42.541Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4307 | 2026-08-15T04:52:47.800Z | external_delegation_updated | ACCEPTING | ACCEPTING | status=active |
| 4308 | 2026-08-15T04:52:48.623Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4309 | 2026-08-15T04:52:49.091Z | usage_event |  |  | status=completed |
| 4310 | 2026-08-15T04:52:49.472Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4311 | 2026-08-15T04:52:54.090Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4312 | 2026-08-15T04:52:54.436Z | usage_event |  |  | status=completed |
| 4313 | 2026-08-15T04:52:54.855Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4314 | 2026-08-15T04:52:59.071Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4315 | 2026-08-15T04:52:59.381Z | usage_event |  |  | status=completed |
| 4316 | 2026-08-15T04:52:59.763Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4317 | 2026-08-15T04:53:15.639Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4318 | 2026-08-15T04:53:15.991Z | usage_event |  |  | status=completed |
| 4319 | 2026-08-15T04:53:15.789Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4320 | 2026-08-15T04:53:20.755Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4321 | 2026-08-15T04:53:20.914Z | usage_event |  |  | status=completed |
| 4322 | 2026-08-15T04:53:21.308Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4323 | 2026-08-15T04:53:26.190Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4324 | 2026-08-15T04:53:26.061Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4325 | 2026-08-15T04:53:26.689Z | usage_event |  |  | status=completed |
| 4326 | 2026-08-15T04:53:31.897Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4327 | 2026-08-15T04:53:32.059Z | usage_event |  |  | status=completed |
| 4328 | 2026-08-15T04:53:32.399Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4329 | 2026-08-15T04:53:37.474Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4330 | 2026-08-15T04:53:37.686Z | usage_event |  |  | status=completed |
| 4331 | 2026-08-15T04:53:38.237Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4332 | 2026-08-15T04:53:49.092Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4333 | 2026-08-15T04:53:49.451Z | usage_event |  |  | status=completed |
| 4334 | 2026-08-15T04:53:49.780Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4335 | 2026-08-15T04:53:54.465Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4336 | 2026-08-15T04:53:54.666Z | usage_event |  |  | status=completed |
| 4337 | 2026-08-15T04:53:55.051Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4338 | 2026-08-15T04:54:04.018Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4339 | 2026-08-15T04:54:04.327Z | usage_event |  |  | status=completed |
| 4340 | 2026-08-15T04:54:04.765Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4341 | 2026-08-15T04:54:09.623Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4342 | 2026-08-15T04:54:09.758Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4343 | 2026-08-15T04:54:10.141Z | usage_event |  |  | status=completed |
| 4344 | 2026-08-15T04:54:19.338Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4345 | 2026-08-15T04:54:19.474Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4346 | 2026-08-15T04:54:19.794Z | usage_event |  |  | status=completed |
| 4347 | 2026-08-15T04:54:27.216Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4348 | 2026-08-15T04:54:27.569Z | usage_event |  |  | status=completed |
| 4349 | 2026-08-15T04:54:27.563Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4350 | 2026-08-15T04:54:32.591Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4351 | 2026-08-15T04:54:32.792Z | usage_event |  |  | status=completed |
| 4352 | 2026-08-15T04:54:33.171Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4353 | 2026-08-15T04:56:23.648Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4354 | 2026-08-15T04:56:23.922Z | external_delegation_started | ACCEPTING | ACCEPTING | status=active |
| 4355 | 2026-08-15T04:56:24.598Z | usage_event |  |  | status=completed |
| 4356 | 2026-08-15T04:56:36.469Z | external_delegation_finished | ACCEPTING | ACCEPTING | status=completed |
| 4357 | 2026-08-15T04:56:37.102Z | usage_event |  |  | status=completed |
| 4358 | 2026-08-15T04:58:54.574Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject diagnostic wave: despite explicit deterministic route and external_review=disabled, 22 OpenCode provider delegations were attributed to this wave with measured provider cost. This violates the no-provider evaluation invariant and invalidates the wave's economics. Stop authority and preserve ledger for root-cause analysis.; failure_class=SOL_REJECTED |
| 4359 | 2026-08-15T04:58:54.794Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6f4f79c194f7b79a | passed | 1fcbbbc59f0763961c197826e9669defc1c82d02f36b2b25a43b25b0bc6e0856 | False | 118 | 0 |
| verify:tests | passed | 0df7eea678679411e29fb3c229075ef6e68f0d3e7643a48aecac3e0706e78b9e | False | 94 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `87`
- Chain head: `64fc2443ea89a350edb6fef0ab2fca4bb10a73921a1cf8a6e06a923d2d83162e`
