# Orchestration Wave 2

- Run: `575caf8c938940b2a9726ec1f6c7f121`
- Wave: `149f5a36988a4d08b3d7b4562ae7cfe1`
- Objective: Add the missing focused regression suite for the already-applied internal Code Mode host-binding proxy. Prove the four allowlisted read-only bindings work, absolute/drive/parent/symlink escapes and exec/mutation/env/network-like operation names fail closed, authorized_roots do not widen Code Mode beyond the primary workspace, request/response caps fail closed, semantic match paths are revalidated, metadata remains gated with host proxy ready/worker isolation missing, and Smart-v3 remains exactly 8 tools with the unchanged contract SHA. Do not alter production source in this wave unless a test demonstrates a real defect. No restart, deploy, commit, push, provider call, or routing change.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `700cf7e699eb993c5ac957a164160cd382a6f70fe9878af28f1afa1c00214acf`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4052 | 2026-08-15T03:22:17.759Z | wave_replanned |  | PREFLIGHT | reason=The previous write-bound proof raced the newly-created test module. The exact focused suite now passes standalone and combined after materialization, with no source change. Record a fresh proof-only wave against the current worktree; do not modify source. |
| 4053 | 2026-08-15T03:22:17.980Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4054 | 2026-08-15T03:22:18.213Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4055 | 2026-08-15T03:22:18.407Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4056 | 2026-08-15T03:22:18.589Z | state_transition | READY | ROUTED | reason=route_selected |
| 4057 | 2026-08-15T03:22:19.124Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=981e11459daf441a9fae0dc42b76ebbf |
| 4058 | 2026-08-15T03:22:19.281Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4059 | 2026-08-15T03:22:19.845Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=981e11459daf441a9fae0dc42b76ebbf |
| 4060 | 2026-08-15T03:22:20.028Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4061 | 2026-08-15T03:22:20.364Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:21121ad2b02c5216; input_fingerprint=569ee21f7f2384ae5757e2c59ae4faf133180ee406f30326e0c87bd373f7bdc0 |
| 4062 | 2026-08-15T03:22:20.934Z | proof_recorded |  |  | stage_id=check:21121ad2b02c5216; status=passed; cache_hit=False; input_fingerprint=569ee21f7f2384ae5757e2c59ae4faf133180ee406f30326e0c87bd373f7bdc0 |
| 4063 | 2026-08-15T03:22:21.218Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=100609ef25a7268198efbd2016dc4f739e3d08fc4d3d5d08488390c0ed2470b5 |
| 4064 | 2026-08-15T03:22:21.791Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=100609ef25a7268198efbd2016dc4f739e3d08fc4d3d5d08488390c0ed2470b5 |
| 4065 | 2026-08-15T03:22:21.947Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=4720af6df96654e1952d101792a09165c14ad50e3059e66bc866d68e47971db4 |
| 4066 | 2026-08-15T03:22:22.476Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=4720af6df96654e1952d101792a09165c14ad50e3059e66bc866d68e47971db4 |
| 4067 | 2026-08-15T03:22:22.712Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4068 | 2026-08-15T03:22:22.865Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:21121ad2b02c5216 | passed | 569ee21f7f2384ae5757e2c59ae4faf133180ee406f30326e0c87bd373f7bdc0 | False | 251 | 0 |
| check:466c2f308b48c766 | passed | 100609ef25a7268198efbd2016dc4f739e3d08fc4d3d5d08488390c0ed2470b5 | False | 276 | 0 |
| verify:tests | failed | 4720af6df96654e1952d101792a09165c14ad50e3059e66bc866d68e47971db4 | False | 172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `da0c868c2612b43965bf8bed4bacc774800338fa4a35d0d32b1d5c6e6b87d314`
