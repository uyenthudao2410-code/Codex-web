# Orchestration Wave 1

- Run: `17385160b7d64d2fae3ed756a6e1799f`
- Wave: `8d443a88654e490c93bd324cd2e61e14`
- Objective: Resume the prepared UI/observability wave after context-ambiguity rejection. Apply only uniquely anchored hunks: governor snapshot correction; sanitized Hub history; Electron typed recovery projection; additive Control Center provider traffic, EOCL phase timing, bounded run history, local recovery and explicit host_not_exposed context-pressure UI; focused tests. Preserve existing concurrent activity-indicator changes and all safety/evidence gates.
- Mode: `mcp_only`
- Base HEAD: `62ff046711503260b079e53a85c66e5b9af01e32`
- Worktree fingerprint: `3e4059b5db65027e9213e01fc0a96cc6309f053018beffdc36a98b2a41812b63`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2242 | 2026-08-14T13:56:17.569Z | run_started |  | PREFLIGHT |  |
| 2243 | 2026-08-14T13:56:17.678Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2244 | 2026-08-14T13:56:17.812Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2245 | 2026-08-14T13:56:17.937Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2246 | 2026-08-14T13:56:18.028Z | state_transition | READY | ROUTED | reason=route_selected |
| 2247 | 2026-08-14T13:56:18.548Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c4b947afbce040c489f7c28741e7bdd5 |
| 2248 | 2026-08-14T13:56:18.676Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2249 | 2026-08-14T13:56:19.321Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c4b947afbce040c489f7c28741e7bdd5 |
| 2250 | 2026-08-14T13:56:19.448Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2251 | 2026-08-14T13:56:21.263Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=66c235a2d5f70f0675bc49009c19f94143a2484cf9bdcdab45bbf1a3a109c34a |
| 2252 | 2026-08-14T13:56:21.370Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 2253 | 2026-08-14T13:56:21.497Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 66c235a2d5f70f0675bc49009c19f94143a2484cf9bdcdab45bbf1a3a109c34a | False | 1343 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `34`
- Chain head: `4abf699026e8e5dbe3e487f2324aa253fb2cdbd1c849c93f3623f514ba413412`
