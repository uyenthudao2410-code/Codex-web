# Orchestration Wave 2

- Run: `3e373f0a22414388be48d9fdf61a2f28`
- Wave: `cc059b9735c7419a9b80f77129510790`
- Objective: Close H0/H1 for ChatWeb controller token measurement with content-free attested envelope evidence. Reuse the existing connector/runtime observation plane; do not add a public tool or infer tokens. Record only whether the exact io.coding-tools/controllerUsage key was present on attested ChatWeb tools/call envelopes, aggregate current-process present/absent counts, expose this in authenticated health and live ChatWeb measurement projection, and explicitly report that no supported post-turn controller-usage sideband exists yet. Preserve existing exact controller UsageEvent ingress and all unrelated dirty hunks. Add focused regressions proving absent envelopes remain unknown/not-zero, present envelopes are observed alongside existing exact usage ingestion, and live projection stays fail-closed.
- Objective revision: `1`
- Objective SHA-256: `2c7bbba402f23976c453a6a2254b457d743dbd162bc428dd322fae3085e98352`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `67e483cebe04c03788e5376d5c309751029a51ed47a15a9a74cc2a2a16fa2ee1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36209 | 2026-09-03T05:00:43.508Z | wave_replanned |  | PREFLIGHT | reason=Previous wave made no source changes and entered REPLAN only because it was recovered outside its original synchronous execution after a pre-write adoption/patch contract failure. Continue with the corrected strategy: patch the current dirty baseline directly without adopt_existing_files, preserving all pre-existing hunks, and run the focused H0/H1 tests. |
| 36210 | 2026-09-03T05:00:43.689Z | observation_span_recorded |  |  |  |
| 36211 | 2026-09-03T05:00:43.978Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36212 | 2026-09-03T05:00:44.204Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36213 | 2026-09-03T05:00:44.432Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36214 | 2026-09-03T05:00:44.583Z | state_transition | READY | ROUTED | reason=route_selected |
| 36215 | 2026-09-03T05:00:44.785Z | observation_span_recorded |  |  |  |
| 36216 | 2026-09-03T05:00:46.374Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a502def7943d4378ba48583228335ff8 |
| 36217 | 2026-09-03T05:00:46.543Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36218 | 2026-09-03T05:00:48.150Z | patch_surface_observed |  |  |  |
| 36219 | 2026-09-03T05:00:48.373Z | observation_span_recorded |  |  |  |
| 36220 | 2026-09-03T05:00:48.943Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a502def7943d4378ba48583228335ff8 |
| 36221 | 2026-09-03T05:00:49.107Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36222 | 2026-09-03T05:00:50.315Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f9e937382cff9e0b270daad4b9e85f81d2fd71f45ba11ede34af70d558c7a5a7 |
| 36223 | 2026-09-03T05:00:50.724Z | managed_process_admitted |  |  | owner=default |
| 36224 | 2026-09-03T05:00:50.977Z | managed_process_started |  |  | owner=default |
| 36225 | 2026-09-03T05:01:39.984Z | managed_process_terminal |  |  | owner=default |
| 36226 | 2026-09-03T05:01:47.148Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f9e937382cff9e0b270daad4b9e85f81d2fd71f45ba11ede34af70d558c7a5a7 |
| 36227 | 2026-09-03T05:01:49.088Z | observation_span_recorded |  |  |  |
| 36228 | 2026-09-03T05:01:49.302Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 36229 | 2026-09-03T05:02:16.984Z | managed_process_admitted |  |  | owner=default |
| 36230 | 2026-09-03T05:02:17.327Z | managed_process_started |  |  | owner=default |
| 36231 | 2026-09-03T05:02:18.033Z | managed_process_terminal |  |  | owner=default |
| 36249 | 2026-09-03T05:03:25.897Z | managed_process_admitted |  |  | owner=default |
| 36250 | 2026-09-03T05:03:26.213Z | managed_process_started |  |  | owner=default |
| 36251 | 2026-09-03T05:03:27.239Z | managed_process_terminal |  |  | owner=default |
| 36252 | 2026-09-03T05:03:39.397Z | quality_outcome_recorded |  |  |  |
| 36253 | 2026-09-03T05:03:39.583Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 36254 | 2026-09-03T05:03:39.905Z | observation_span_recorded |  |  |  |
| 36255 | 2026-09-03T05:03:40.147Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f9e937382cff9e0b270daad4b9e85f81d2fd71f45ba11ede34af70d558c7a5a7 | False | 56343 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 4c26c8e0db9448399d6acc0b0e0275e4 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | da47a9ea24138318d6bf2b7bbb200184a1be34795c2fe499e1db1698345df109 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `2753f63a47fcafff15213b8a3aa8b83fb318aa46355e7674dbb37363652ac235`
