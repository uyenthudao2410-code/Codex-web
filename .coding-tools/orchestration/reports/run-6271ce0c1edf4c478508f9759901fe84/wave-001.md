# Orchestration Wave 1

- Run: `6271ce0c1edf4c478508f9759901fe84`
- Wave: `1886b1f3b7f744df9a8c502e928c963e`
- Objective: Fix the pre-existing Windows runner test-harness inconsistency exposed by the broad current-head suite. The production platform policy intentionally uses USERPROFILE and ignores HOME on Windows. Update only crates/webcodex-runner/src/main_tests.rs so the empty-allowed-roots default test derives the expected platform home through agent_init::home_allowed_root(), and make the three shared TEST_ENV_LOCK acquisitions poison-tolerant so one assertion cannot cascade into unrelated failures. Do not change production home/path policy or Wave A/B/C behavior. Preserve unrelated runtime evidence and local commits.
- Objective revision: `1`
- Objective SHA-256: `7e609d473257e68a3632a278bec2330359ff64758506f7e48edbc7d11ae3f17c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `d15983737106fb33595b75bba01e718cefaf3682`
- Worktree fingerprint: `315a0b960a9c6d6dfcc560dcfd65cb216d109ce74339f63d854f1a341b954c29`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27126 | 2026-08-22T11:52:28.976Z | run_started |  | PREFLIGHT |  |
| 27127 | 2026-08-22T11:52:41.456Z | solution_shadow_recommended |  |  |  |
| 27128 | 2026-08-22T11:52:56.901Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27129 | 2026-08-22T11:52:57.041Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27130 | 2026-08-22T11:52:57.207Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 27131 | 2026-08-22T11:52:57.376Z | state_transition | READY | ROUTED | reason=route_selected |
| 27132 | 2026-08-22T11:52:58.221Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b0e1a32e13c04354b3f05f34a79cce6a |
| 27133 | 2026-08-22T11:52:58.364Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27134 | 2026-08-22T11:52:59.070Z | patch_surface_observed |  |  |  |
| 27135 | 2026-08-22T11:52:59.376Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b0e1a32e13c04354b3f05f34a79cce6a |
| 27136 | 2026-08-22T11:52:59.526Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27137 | 2026-08-22T11:53:00.177Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9e336a26865bb8318c373241307de9dcfa3150bcb2bfe3569581112be07d5174 |
| 27138 | 2026-08-22T11:53:00.514Z | managed_process_admitted |  |  | owner=default |
| 27139 | 2026-08-22T11:53:00.776Z | managed_process_started |  |  | owner=default |
| 27140 | 2026-08-22T11:53:12.790Z | managed_process_terminal |  |  | owner=default |
| 27141 | 2026-08-22T11:53:21.387Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9e336a26865bb8318c373241307de9dcfa3150bcb2bfe3569581112be07d5174 |
| 27142 | 2026-08-22T11:53:22.399Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 27143 | 2026-08-22T12:29:16.645Z | quality_outcome_recorded |  |  |  |
| 27144 | 2026-08-22T12:29:16.773Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 27145 | 2026-08-22T12:29:17.105Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 9e336a26865bb8318c373241307de9dcfa3150bcb2bfe3569581112be07d5174 | False | 20000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 742585470a7f427f8a743fe2d43b53e0 | accepted | d15983737106fb33595b75bba01e718cefaf3682 | 896e8f596af8f704bb8264a07e371730a1e0c593eacc9e213048569819f37d57 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `4541e44a897853dbf91498abbca23662729d2d4578644cef024a271964f3ab6c`
