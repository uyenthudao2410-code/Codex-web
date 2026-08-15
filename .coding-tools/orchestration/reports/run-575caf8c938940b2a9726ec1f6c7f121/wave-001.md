# Orchestration Wave 1

- Run: `575caf8c938940b2a9726ec1f6c7f121`
- Wave: `655cd8bb38e8477d9a6c6618b69befb2`
- Objective: Add the missing focused regression suite for the already-applied internal Code Mode host-binding proxy. Prove the four allowlisted read-only bindings work, absolute/drive/parent/symlink escapes and exec/mutation/env/network-like operation names fail closed, authorized_roots do not widen Code Mode beyond the primary workspace, request/response caps fail closed, semantic match paths are revalidated, metadata remains gated with host proxy ready/worker isolation missing, and Smart-v3 remains exactly 8 tools with the unchanged contract SHA. Do not alter production source in this wave unless a test demonstrates a real defect. No restart, deploy, commit, push, provider call, or routing change.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `b6675f252823732ea8d4b33a8fee2a413a468e4fd9cd040700162634befadb25`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4035 | 2026-08-15T03:21:39.700Z | run_started |  | PREFLIGHT |  |
| 4036 | 2026-08-15T03:21:39.886Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4037 | 2026-08-15T03:21:40.074Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4038 | 2026-08-15T03:21:40.306Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4039 | 2026-08-15T03:21:40.552Z | state_transition | READY | ROUTED | reason=route_selected |
| 4040 | 2026-08-15T03:21:41.077Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1cbf13530667495cabf7153543f7e4f9 |
| 4041 | 2026-08-15T03:21:41.259Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4042 | 2026-08-15T03:21:41.830Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1cbf13530667495cabf7153543f7e4f9 |
| 4043 | 2026-08-15T03:21:42.025Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4044 | 2026-08-15T03:21:42.413Z | proof_cache_miss |  |  | reason=cold; stage_id=check:21121ad2b02c5216; input_fingerprint=09f3d9e3f6318e2cf241b7a5e4941758796ddc38637b89000b97d29708014f08 |
| 4045 | 2026-08-15T03:21:43.052Z | proof_recorded |  |  | stage_id=check:21121ad2b02c5216; status=passed; cache_hit=False; input_fingerprint=09f3d9e3f6318e2cf241b7a5e4941758796ddc38637b89000b97d29708014f08 |
| 4046 | 2026-08-15T03:21:43.266Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=c94dbbab0fa106ad18ef55f122cb5f14d45a94b90752e07c3ba82a30689f7ca5 |
| 4047 | 2026-08-15T03:21:43.894Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=c94dbbab0fa106ad18ef55f122cb5f14d45a94b90752e07c3ba82a30689f7ca5 |
| 4048 | 2026-08-15T03:21:44.092Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=d706f50d5ef49b849659b6afc50ab78d3268036493e8797b29c8cc0332859031 |
| 4049 | 2026-08-15T03:21:44.639Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=d706f50d5ef49b849659b6afc50ab78d3268036493e8797b29c8cc0332859031 |
| 4050 | 2026-08-15T03:21:44.842Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4051 | 2026-08-15T03:21:45.064Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:21121ad2b02c5216 | passed | 09f3d9e3f6318e2cf241b7a5e4941758796ddc38637b89000b97d29708014f08 | False | 289 | 0 |
| check:466c2f308b48c766 | passed | c94dbbab0fa106ad18ef55f122cb5f14d45a94b90752e07c3ba82a30689f7ca5 | False | 295 | 0 |
| verify:tests | failed | d706f50d5ef49b849659b6afc50ab78d3268036493e8797b29c8cc0332859031 | False | 188 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `da0c868c2612b43965bf8bed4bacc774800338fa4a35d0d32b1d5c6e6b87d314`
