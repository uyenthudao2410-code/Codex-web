# Orchestration Wave 1

- Run: `0e6eed197f63440bbf0aaa90cc8da3df`
- Wave: `21adaa7d41e54df4a199fe0bffee6ca0`
- Objective: Audit the existing experimental Code Mode seam and design the smallest safe implementation path that can be completed source-side now without enabling it. Locate experimental_code_mode metadata, any worker/process isolation primitives, host bindings, execution handlers, sandbox/process crates, and tests. Required boundary: isolated worker with host-bindings-only access; no direct filesystem, network, environment secrets, or unrestricted subprocess. Preserve Smart-v3 8-tool surface and current authorization/EOCL semantics. Return exact files/symbols, whether the boundary can be implemented with existing primitives, and the smallest behavior packet/proof. Do not mutate source yet.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `a7bc4ba1cb8fbbab8549e1ff358f7a276b14a3a5836a5ee0f1df09fd035061bf`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4016 | 2026-08-15T03:18:11.161Z | run_started |  | PREFLIGHT |  |
| 4017 | 2026-08-15T03:18:11.901Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4018 | 2026-08-15T03:18:32.265Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4019 | 2026-08-15T03:20:43.315Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4020 | 2026-08-15T03:20:43.516Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4021 | 2026-08-15T03:20:43.699Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4022 | 2026-08-15T03:20:43.872Z | state_transition | READY | ROUTED | reason=route_selected |
| 4023 | 2026-08-15T03:20:44.409Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7002a9b482924538983c829d5dd5c318 |
| 4024 | 2026-08-15T03:20:44.659Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4025 | 2026-08-15T03:20:45.396Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7002a9b482924538983c829d5dd5c318 |
| 4026 | 2026-08-15T03:20:45.595Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4027 | 2026-08-15T03:20:45.985Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3f9712d24e9eaeee; input_fingerprint=7946adfe47da8128e541d7864e4ec23b83ea35a984d553d46f23642d44689db6 |
| 4028 | 2026-08-15T03:20:46.619Z | proof_recorded |  |  | stage_id=check:3f9712d24e9eaeee; status=passed; cache_hit=False; input_fingerprint=7946adfe47da8128e541d7864e4ec23b83ea35a984d553d46f23642d44689db6 |
| 4029 | 2026-08-15T03:20:46.851Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=8185011ab5ed3a0df942cd659884139fb5031b8a8a3b2ec4c8de934e98d40549 |
| 4030 | 2026-08-15T03:20:47.502Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=8185011ab5ed3a0df942cd659884139fb5031b8a8a3b2ec4c8de934e98d40549 |
| 4031 | 2026-08-15T03:20:47.709Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2f77e79048c1dd97f081d51d2072c77633331ac5078477f33c39b54579b2adb6 |
| 4032 | 2026-08-15T03:20:48.237Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=2f77e79048c1dd97f081d51d2072c77633331ac5078477f33c39b54579b2adb6 |
| 4033 | 2026-08-15T03:20:48.442Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4034 | 2026-08-15T03:20:48.618Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:3f9712d24e9eaeee | passed | 7946adfe47da8128e541d7864e4ec23b83ea35a984d553d46f23642d44689db6 | False | 261 | 0 |
| check:466c2f308b48c766 | passed | 8185011ab5ed3a0df942cd659884139fb5031b8a8a3b2ec4c8de934e98d40549 | False | 292 | 0 |
| verify:tests | failed | 2f77e79048c1dd97f081d51d2072c77633331ac5078477f33c39b54579b2adb6 | False | 172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `295f50e5c6535bc9db7cd30ea27e0d4a9141bb2d416dc4b62424972ae46f7ee0`
