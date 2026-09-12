# Orchestration Wave 2

- Run: `306c03f544ba4af6bf1de8777045d227`
- Wave: `2c7a5f67f77c47778062e7fe72445367`
- Objective: Packet C4: create a new bugfix RUN without reopening or amending accepted C2. Fix the real ABA fencing defect in resources/coding-tools-mcp/coding_tools_mcp/run_continuation.py and resources/coding-tools-mcp/tests/test_run_continuation.py only. Current behavior: revoke/regrant resets driver_generation=0, so after policy revision 2 a claim by the same runtime_instance_id can receive generation=1 again, allowing an old worker with the same runtime ID and generation to pass assert_run_continuation_execution, reserve a new action, and bind stale dispatch identity. Minimal fix: on regrant do not reset driver_generation to 0; preserve monotonic generation across revoke/regrant, and require the next claim to use the observed current generation as expected_generation then increment. Preserve the no-pending-effects/job gate, full immutable policy behavior, fencing, effect history, schema, public tool surface, and all unrelated behavior. Update the existing C2 regrant regression that hardcodes expected_generation=0 to use the observed new-policy generation without weakening its assertions. Add a focused regression using the same runtime_instance_id proving the old generation is rejected after revoke->regrant->reclaim at assert, reserve, and dispatch boundaries, while the fresh generation can proceed. Do not use any continuation/background driver to modify runtime. Do not touch .coding-tools or any other source file directly. Prepare only in this call; no patch, no proof, no accept, no commit, no restart.
- Objective revision: `1`
- Objective SHA-256: `be8d10a3426b87f376fa004736b1b44c0bd93cb72e447e4f9832cf37e639c2ec`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `dfb502935ae9b720966b23687cc08d9278845bb9db66c59ac1fbc6cb54409c2c`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43657 | 2026-09-08T02:04:40.682Z | wave_replanned |  | PREFLIGHT | reason=ACCEPTANCE_FILE_ATTESTATION_REQUIRED provenance recovery |
| 43658 | 2026-09-08T02:04:40.861Z | observation_span_recorded |  |  |  |
| 43659 | 2026-09-08T02:04:41.054Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43660 | 2026-09-08T02:04:41.204Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43661 | 2026-09-08T02:04:41.360Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43662 | 2026-09-08T02:04:41.528Z | state_transition | READY | ROUTED | reason=route_selected |
| 43663 | 2026-09-08T02:04:41.729Z | observation_span_recorded |  |  |  |
| 43664 | 2026-09-08T02:04:42.460Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f3985b3879f04a399e2933f26917619e |
| 43665 | 2026-09-08T02:04:42.604Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43666 | 2026-09-08T02:04:43.204Z | existing_file_adoption_observed |  |  |  |
| 43667 | 2026-09-08T02:04:43.386Z | observation_span_recorded |  |  |  |
| 43668 | 2026-09-08T02:04:43.678Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f3985b3879f04a399e2933f26917619e |
| 43669 | 2026-09-08T02:04:43.845Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43670 | 2026-09-08T02:04:44.460Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=9240677dffe2f50ce4fdfdf131e28a1f87495ea8f385f1c7e99594dead91ebe3 |
| 43671 | 2026-09-08T02:04:44.804Z | managed_process_admitted |  |  | owner=default |
| 43672 | 2026-09-08T02:04:45.113Z | managed_process_started |  |  | owner=default |
| 43673 | 2026-09-08T02:06:43.184Z | managed_process_terminal |  |  | owner=default |
| 43674 | 2026-09-08T02:06:43.577Z | managed_process_admitted |  |  | owner=default |
| 43675 | 2026-09-08T02:06:44.169Z | managed_process_started |  |  | owner=default |
| 43676 | 2026-09-08T02:16:43.724Z | managed_process_terminal |  |  | owner=default |
| 43677 | 2026-09-08T02:16:44.050Z | proof_recorded |  |  | stage_id=verify:all; status=failed; cache_hit=False; input_fingerprint=9240677dffe2f50ce4fdfdf131e28a1f87495ea8f385f1c7e99594dead91ebe3 |
| 43678 | 2026-09-08T02:16:44.278Z | observation_span_recorded |  |  |  |
| 43679 | 2026-09-08T02:16:44.460Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 43680 | 2026-09-08T02:16:44.618Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 43681 | 2026-09-08T02:16:44.818Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 43696 | 2026-09-08T04:52:56.674Z | state_transition | REPLAN | ABORTED | reason=C4_SUPERSEDED_BY_BROADER_CONTINUATION_RECOVERY_AND_PROVENANCE_HARDENING |
| 43697 | 2026-09-08T04:52:57.066Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:all | failed | 9240677dffe2f50ce4fdfdf131e28a1f87495ea8f385f1c7e99594dead91ebe3 | False | 719264 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `68`
- Chain head: `cd498cc1b84d4cb7522d165c81a89fe8fb73b9fe14c2175f252fa7ffb0d6ef90`
