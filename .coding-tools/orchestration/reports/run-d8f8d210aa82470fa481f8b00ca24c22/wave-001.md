# Orchestration Wave 1

- Run: `d8f8d210aa82470fa481f8b00ca24c22`
- Wave: `f697523d0ebc4d019171c6b104737612`
- Objective: Re-prove the command_control TaskState terminalization fix already present in the worktree. No source changes in this wave. Verify terminal poll clears current_command, preserves ArtifactRef/result, and terminal orchestration is not downgraded.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `23806b352cf045a12d7a6a582fd22aee676c8c347b370aad73f6776e4f10e79b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3190 | 2026-08-14T17:55:19.059Z | run_started |  | PREFLIGHT |  |
| 3191 | 2026-08-14T17:55:19.200Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3192 | 2026-08-14T17:55:19.350Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3193 | 2026-08-14T17:55:19.533Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 3194 | 2026-08-14T17:55:19.644Z | state_transition | READY | ROUTED | reason=route_selected |
| 3195 | 2026-08-14T17:55:20.099Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=17569bb1de644dec9b59bf14343bb15e |
| 3196 | 2026-08-14T17:55:20.232Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3197 | 2026-08-14T17:55:20.683Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=17569bb1de644dec9b59bf14343bb15e |
| 3198 | 2026-08-14T17:55:20.834Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3199 | 2026-08-14T17:55:21.246Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d4ee081147d953a9; input_fingerprint=b28c128c4902b63e006f7ec8e270fa269f6407a5dfd50ef39838a9fa3dd96efd |
| 3200 | 2026-08-14T17:55:22.117Z | proof_recorded |  |  | stage_id=check:d4ee081147d953a9; status=passed; cache_hit=False; input_fingerprint=b28c128c4902b63e006f7ec8e270fa269f6407a5dfd50ef39838a9fa3dd96efd |
| 3201 | 2026-08-14T17:55:22.302Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3202 | 2026-08-14T17:57:07.989Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d4ee081147d953a9 | passed | b28c128c4902b63e006f7ec8e270fa269f6407a5dfd50ef39838a9fa3dd96efd | False | 627 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ec845caf11a84c1d964f4faa6aee36dd | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 44794c9e68d11873173a9a7201f7886fd3dbb073db108730be2e17f279bc7ad3 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `4f08c36b97da73ef520eceba4152fe7955e4d1c306ca0cb53e7e3ffee5ebd5b8`
