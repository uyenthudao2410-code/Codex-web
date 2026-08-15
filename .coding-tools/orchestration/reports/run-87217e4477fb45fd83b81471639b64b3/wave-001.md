# Orchestration Wave 1

- Run: `87217e4477fb45fd83b81471639b64b3`
- Wave: `189eb4e8f4cd4034a763cbc83c071372`
- Objective: Protect performance/cost measurement integrity. Prevent uncorrelated OpenCode provider telemetry from being attributed to a non-OpenCode active EOCL wave; preserve intentional uncorrelated telemetry only when the wave itself is explicitly routed to OpenCode. Separate measured provider cost coverage from causal task attribution so total accepted-result cost is incomplete when provider usage is not dispatch-correlated. Harden the OpenCode timeout fixture against broad-suite scheduler delay without weakening the expected timeout classification. Do not call any external model/provider or external review.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `86ae8a02f3d122cfb843373105bb2797398b5030b7b7a079dd918ec784dafcc5`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4370 | 2026-08-15T05:05:19.029Z | run_started |  | PREFLIGHT |  |
| 4371 | 2026-08-15T05:05:19.188Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4372 | 2026-08-15T05:05:19.400Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4373 | 2026-08-15T05:05:19.627Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4374 | 2026-08-15T05:05:19.851Z | state_transition | READY | ROUTED | reason=route_selected |
| 4375 | 2026-08-15T05:05:20.436Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0126dfbe51c74740a9d5501d80efa6e6 |
| 4376 | 2026-08-15T05:05:20.675Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4377 | 2026-08-15T05:05:21.478Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0126dfbe51c74740a9d5501d80efa6e6 |
| 4378 | 2026-08-15T05:05:21.653Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4379 | 2026-08-15T05:05:22.367Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=461600ae30aa663fab04792b435f6386b4dab88d9a9c2005cf60c423b17b930f |
| 4380 | 2026-08-15T05:05:23.207Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=461600ae30aa663fab04792b435f6386b4dab88d9a9c2005cf60c423b17b930f |
| 4381 | 2026-08-15T05:05:23.470Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=506bcb821eeff5f674ad84fd1b5556ca03644dae37419efd82e2e56ba25e9661 |
| 4382 | 2026-08-15T05:05:42.550Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=506bcb821eeff5f674ad84fd1b5556ca03644dae37419efd82e2e56ba25e9661 |
| 4383 | 2026-08-15T05:05:42.763Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4384 | 2026-08-15T05:05:42.999Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 461600ae30aa663fab04792b435f6386b4dab88d9a9c2005cf60c423b17b930f | False | 503 | 0 |
| verify:tests | failed | 506bcb821eeff5f674ad84fd1b5556ca03644dae37419efd82e2e56ba25e9661 | False | 18702 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `869497f91fe3c739c885bdcb1b35f818b05d5b28869f84f9c7e3fe709e9a355d`
