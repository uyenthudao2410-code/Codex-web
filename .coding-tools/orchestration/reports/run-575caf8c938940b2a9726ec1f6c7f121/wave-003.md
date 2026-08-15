# Orchestration Wave 3

- Run: `575caf8c938940b2a9726ec1f6c7f121`
- Wave: `46487869409b4f3ba6c39fb6be1ec504`
- Objective: Add the missing focused regression suite for the already-applied internal Code Mode host-binding proxy. Prove the four allowlisted read-only bindings work, absolute/drive/parent/symlink escapes and exec/mutation/env/network-like operation names fail closed, authorized_roots do not widen Code Mode beyond the primary workspace, request/response caps fail closed, semantic match paths are revalidated, metadata remains gated with host proxy ready/worker isolation missing, and Smart-v3 remains exactly 8 tools with the unchanged contract SHA. Do not alter production source in this wave unless a test demonstrates a real defect. No restart, deploy, commit, push, provider call, or routing change.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `700cf7e699eb993c5ac957a164160cd382a6f70fe9878af28f1afa1c00214acf`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4069 | 2026-08-15T03:22:40.094Z | wave_replanned |  | PREFLIGHT | reason=The EOCL verifier executes its test command from repository root despite the supplied workdir, so `tests.*` resolved against the root test package and produced import errors. The identical oracle passes when run from resources/coding-tools-mcp. Change only the proof commands to include an explicit cwd; source and tests are unchanged. |
| 4070 | 2026-08-15T03:22:40.340Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4071 | 2026-08-15T03:22:40.491Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4072 | 2026-08-15T03:22:40.657Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4073 | 2026-08-15T03:22:40.810Z | state_transition | READY | ROUTED | reason=route_selected |
| 4074 | 2026-08-15T03:22:41.297Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f379ef71a4d948a8b6c3db91df060232 |
| 4075 | 2026-08-15T03:22:41.453Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4076 | 2026-08-15T03:22:42.030Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f379ef71a4d948a8b6c3db91df060232 |
| 4077 | 2026-08-15T03:22:42.197Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4078 | 2026-08-15T03:22:42.560Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2a1162e9dae1d025; input_fingerprint=bb622cf491703e898895ce6b1eb92c71e9ff719a6873a4f41640a547ec82b371 |
| 4079 | 2026-08-15T03:22:43.149Z | proof_recorded |  |  | stage_id=check:2a1162e9dae1d025; status=passed; cache_hit=False; input_fingerprint=bb622cf491703e898895ce6b1eb92c71e9ff719a6873a4f41640a547ec82b371 |
| 4080 | 2026-08-15T03:22:43.317Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=b4d1da5118a2760161ba2664ddb5f9870a9abbc6bd7df3c5829d5658695ed9e8 |
| 4081 | 2026-08-15T03:22:43.900Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=b4d1da5118a2760161ba2664ddb5f9870a9abbc6bd7df3c5829d5658695ed9e8 |
| 4082 | 2026-08-15T03:22:44.091Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2ce2c28a5df86225db8777c8a4bf3fb1ca9e59ae1a95261a5d599a8984cd4709 |
| 4083 | 2026-08-15T03:22:46.084Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2ce2c28a5df86225db8777c8a4bf3fb1ca9e59ae1a95261a5d599a8984cd4709 |
| 4084 | 2026-08-15T03:22:46.282Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4085 | 2026-08-15T03:25:28.833Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2a1162e9dae1d025 | passed | bb622cf491703e898895ce6b1eb92c71e9ff719a6873a4f41640a547ec82b371 | False | 276 | 0 |
| check:466c2f308b48c766 | passed | b4d1da5118a2760161ba2664ddb5f9870a9abbc6bd7df3c5829d5658695ed9e8 | False | 277 | 0 |
| verify:tests | passed | 2ce2c28a5df86225db8777c8a4bf3fb1ca9e59ae1a95261a5d599a8984cd4709 | False | 1641 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f9c9af20fbdd47cbac754517b5fc349f | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 5bff450f5524e2e611a2bd7d7db361f761d6404c82ecd4664b6f9150b19a07b2 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `51`
- Chain head: `da0c868c2612b43965bf8bed4bacc774800338fa4a35d0d32b1d5c6e6b87d314`
