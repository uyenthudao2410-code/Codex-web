# Orchestration Wave 1

- Run: `170c7aa1bdfe4da4827ea9101dadfda7`
- Wave: `4be5f54ef42344c3b4a0b5e23e34ccb8`
- Objective: P1C inspect the existing Windows build/package/install-smoke path and identify the smallest exact-source provenance insertion point. Required identity: exact Git SHA plus clean/source fingerprint, app version, Coding Tools MCP version/build identity, native artifact SHA-256 values, the actual npm/installer candidate SHA-256, and canonical proof identity. The smoke-tested candidate bytes must be the provenance-described bytes. Do not mutate in prepare and do not publish/release/tag/push.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `6013c41933e2fdca8f9331687839dde9070c3f4d35bfa4fd0e861205434031c7`
- Contract fingerprint: `56e43a1eca5142b7c5f20eaa1f3002e0c6193c6d8813ac183f0460eba8748b9d`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3826 | 2026-08-15T02:29:40.358Z | run_started |  | PREFLIGHT |  |
| 3827 | 2026-08-15T02:29:41.144Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 3828 | 2026-08-15T02:33:00.716Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3829 | 2026-08-15T02:33:00.923Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3830 | 2026-08-15T02:33:01.089Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3831 | 2026-08-15T02:33:01.306Z | state_transition | READY | ROUTED | reason=route_selected |
| 3832 | 2026-08-15T02:33:01.850Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c308bfeb11614c69910755d6e5832349 |
| 3833 | 2026-08-15T02:33:02.000Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3834 | 2026-08-15T02:33:02.843Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c308bfeb11614c69910755d6e5832349 |
| 3835 | 2026-08-15T02:33:02.982Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3836 | 2026-08-15T02:33:03.361Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=87c52d184eb35d1a16bc42fecdab4e286b93c282bbb473331c510be329472548 |
| 3837 | 2026-08-15T02:33:03.906Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=87c52d184eb35d1a16bc42fecdab4e286b93c282bbb473331c510be329472548 |
| 3838 | 2026-08-15T02:33:04.034Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 3839 | 2026-08-15T02:33:04.215Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 87c52d184eb35d1a16bc42fecdab4e286b93c282bbb473331c510be329472548 | False | 266 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `3e031afd248135cd62d49908953ac61389ac44f7f441bece70a4f7e20391781c`
