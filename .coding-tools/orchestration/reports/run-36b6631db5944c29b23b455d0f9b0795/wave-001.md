# Orchestration Wave 1

- Run: `36b6631db5944c29b23b455d0f9b0795`
- Wave: `3d398b5a8c9f4915aee78724f80bd9aa`
- Objective: Fix the live Phase 3A Install runtime failure without changing supervisor policy. Normalize every custom PowerShell helper invocation that uses method-like `FunctionName(...)` syntax into idiomatic command syntax with a separating space/parenthesized argument, especially Assert-Manifest, Test-AbsoluteSafePath, Test-PathEqual, Get-Sha256File, and Get-Sha256Text in Install/Status/Uninstall/Run paths. Add a static regression to reject method-like calls for those helpers. Preserve all fail-closed health/restart behavior and unrelated runtime evidence. Prove PowerShell AST parse, focused supervisor tests, and full npm test.
- Mode: `mcp_only`
- Base HEAD: `6299c052567852607ddcda30fabe48c859eef932`
- Worktree fingerprint: `25402d5abb7e1ead012b327eb0ff1ee549f47ad4549c5a0e75b83571476cdc79`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6398 | 2026-08-16T08:45:31.231Z | run_started |  | PREFLIGHT |  |
| 6399 | 2026-08-16T08:45:31.579Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6400 | 2026-08-16T08:45:31.717Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6401 | 2026-08-16T08:45:31.831Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6402 | 2026-08-16T08:45:31.956Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6403 | 2026-08-16T08:45:32.089Z | state_transition | READY | ROUTED | reason=route_selected |
| 6404 | 2026-08-16T08:45:32.472Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=be095f9328dc48e8af31e5b4e65f0a08 |
| 6405 | 2026-08-16T08:45:32.581Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6406 | 2026-08-16T08:45:32.998Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=be095f9328dc48e8af31e5b4e65f0a08 |
| 6407 | 2026-08-16T08:45:33.124Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6408 | 2026-08-16T08:45:33.439Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d9c099758f2ff7c2; input_fingerprint=2f13eb10f6fade9ead4ce697640808a002f11fd2431f3b4f82f1bbac28f0cf24 |
| 6409 | 2026-08-16T08:45:33.682Z | managed_process_admitted |  |  | owner=default |
| 6410 | 2026-08-16T08:45:33.910Z | managed_process_started |  |  | owner=default |
| 6411 | 2026-08-16T08:45:34.427Z | managed_process_terminal |  |  | owner=default |
| 6412 | 2026-08-16T08:45:34.686Z | proof_recorded |  |  | stage_id=check:d9c099758f2ff7c2; status=passed; cache_hit=False; input_fingerprint=2f13eb10f6fade9ead4ce697640808a002f11fd2431f3b4f82f1bbac28f0cf24 |
| 6413 | 2026-08-16T08:45:34.845Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=ff7ff3f374372dc05e01ab52295b3a59464ec088b7e16285f8c6ccdfea48a6fb |
| 6414 | 2026-08-16T08:45:35.109Z | managed_process_admitted |  |  | owner=default |
| 6415 | 2026-08-16T08:45:35.360Z | managed_process_started |  |  | owner=default |
| 6416 | 2026-08-16T08:45:37.948Z | managed_process_terminal |  |  | owner=default |
| 6417 | 2026-08-16T08:45:38.228Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=failed; cache_hit=False; input_fingerprint=ff7ff3f374372dc05e01ab52295b3a59464ec088b7e16285f8c6ccdfea48a6fb |
| 6418 | 2026-08-16T08:45:38.378Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 6419 | 2026-08-16T08:45:38.533Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 6420 | 2026-08-16T08:45:38.685Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9c099758f2ff7c2 | passed | 2f13eb10f6fade9ead4ce697640808a002f11fd2431f3b4f82f1bbac28f0cf24 | False | 996 | 0 |
| check:fe3ffbf7aa7a92a6 | failed | ff7ff3f374372dc05e01ab52295b3a59464ec088b7e16285f8c6ccdfea48a6fb | False | 3124 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `96ad1d8eab742b569bd4899cd59cb5ff1f3ef0cb65eff7c936c9ef9dcaf2e0c0`
