# Orchestration Wave 1

- Run: `1b4ecb6beb324d3f9d87d506c6b682b8`
- Wave: `6ba9213f91cb4b038cf65f0673640220`
- Objective: Execute the final P1.1 exact-fingerprint RC source/security matrix on the newly accepted harness-compatible worktree. Run all maintained non-packaging gates in fail-closed order: diff hygiene, full Node/Electron tests and source-root-clean guard, full Coding MCP pytest, Recovery E2E, OpenCode Flash preflight only with no provider dispatch/cost, and production dependency audit. Do not mutate source/docs, do not build final installer yet, do not commit/push/restart/deploy/release/tag/publish, and preserve the resident codex-app-server and all .coding-tools evidence.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `5d67997ad61099790a0cddf44d653793e24e3363df3cc3e391a268c7218baeea`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25744 | 2026-08-21T04:09:29.983Z | run_started |  | PREFLIGHT |  |
| 25745 | 2026-08-21T04:09:30.362Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25746 | 2026-08-21T04:09:30.535Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25747 | 2026-08-21T04:09:30.703Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25748 | 2026-08-21T04:09:30.851Z | state_transition | READY | ROUTED | reason=route_selected |
| 25749 | 2026-08-21T04:09:31.273Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c74f4cc56d95481594f7821975c5902d |
| 25750 | 2026-08-21T04:09:31.416Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25751 | 2026-08-21T04:09:31.833Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c74f4cc56d95481594f7821975c5902d |
| 25752 | 2026-08-21T04:09:31.979Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25753 | 2026-08-21T04:09:32.356Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=2d571749e1b1785d45a66feeb22bac9ae15120a836534039528ffc386f0ecfd5 |
| 25754 | 2026-08-21T04:09:32.737Z | managed_process_admitted |  |  | owner=default |
| 25755 | 2026-08-21T04:09:33.105Z | managed_process_started |  |  | owner=default |
| 25756 | 2026-08-21T04:09:34.024Z | managed_process_terminal |  |  | owner=default |
| 25757 | 2026-08-21T04:09:34.411Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=2d571749e1b1785d45a66feeb22bac9ae15120a836534039528ffc386f0ecfd5 |
| 25758 | 2026-08-21T04:09:34.570Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=45cdd350e6aa048403176d848d8c6e26d6688ac3d7333e75f8dd30fa8bddc382 |
| 25759 | 2026-08-21T04:09:34.961Z | managed_process_admitted |  |  | owner=default |
| 25760 | 2026-08-21T04:09:35.230Z | managed_process_started |  |  | owner=default |
| 25761 | 2026-08-21T04:09:55.777Z | managed_process_terminal |  |  | owner=default |
| 25762 | 2026-08-21T04:09:56.676Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=failed; cache_hit=False; input_fingerprint=45cdd350e6aa048403176d848d8c6e26d6688ac3d7333e75f8dd30fa8bddc382 |
| 25763 | 2026-08-21T04:09:57.877Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 25764 | 2026-08-21T04:09:58.006Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 25765 | 2026-08-21T04:09:58.180Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 2d571749e1b1785d45a66feeb22bac9ae15120a836534039528ffc386f0ecfd5 | False | 1664 | 0 |
| check:328e123c63857fd8 | failed | 45cdd350e6aa048403176d848d8c6e26d6688ac3d7333e75f8dd30fa8bddc382 | False | 21252 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `16fdcef5028739369547124b45fb8b48e2874a0403c7972dc2f481620855f428`
