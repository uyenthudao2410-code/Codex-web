# Orchestration Wave 3

- Run: `4b1f597e74d54742b04f726cab5e665e`
- Wave: `e614b70c0d0e4e68a07b10c6b3c1dfcf`
- Objective: Fresh EOCL RUN/WAVE only; do not reuse or mutate any prior accepted-code activation intent. Residual bugfix: close the fail-closed persistence gap in RecoveryActionStore durable_epoch_binding. PRE-MUTATION HARD GATE: the two owned dirty files must exactly match accepted checkpoint c213617ecc4941ac907433e69bc64e6c receipts before any write: electron/services/recoveryActionStore.js sha256=0e857c5e7d3932bcbc08832e5d9fff4737db0d01c489dac3f06e208d0e661872 and tests/recovery-activation.test.js sha256=062e6653574e8be1966f26215f121843fdfcf64d57a870918c309cc7ade658c4. Use exact-byte adoption as the preimage gate and stop on mismatch. Own and mutate ONLY those two paths; acquire a write lease scoped to exactly those two paths; do not touch recoveryActivation.js or any other concurrent WIP.

Required semantics: (1) preserve the existing compatible three-field durable_epoch_binding shape across Recovery Host handoff; do not add required persisted fields. (2) At load/use time, durableEpochBinding must require safe created_at_unix_ms from the action record and reject a durable expiry beyond a deterministic persisted lifetime cap derived from action creation + MAX_DURABLE_EPOCH_TTL_MS + at most the authenticated request admission window of 60 seconds. Introduce an explicitly named constant for that admission allowance; cap must stay bounded and fail-closed. (3) bindDurableEpoch must enforce the same persisted cap in addition to its existing now-relative 10-minute check; preserve immutable request expires_at_unix_ms and exact operation/epoch validation. (4) Malformed, identity-mismatched, or over-bound stored binding is non-authoritative: replay/get/active fall back to request expiry and, once that expires, terminalize ACTIVATION_REQUEST_EXPIRED; never trust the tampered durable deadline. (5) Add focused regressions proving a valid existing three-field binding remains active after request expiry but before epoch expiry, and a tampered over-bound stored three-field binding is rejected as authority and expires on the original request deadline. Implement the smallest coherent patch.

Proof must run in this exact order after mutation: node --test tests/recovery-activation.test.js; then node --test tests/accepted-code-activation.test.js; then scoped git diff --check for the two owned paths. Produce exact-byte receipts/fingerprints, reach ACCEPTING, release/quiesce write resources, and STOP for ChatWeb Sol/user explicit acceptance. Do NOT self-accept or reject. No direct ledger/projection/runtime-state edits, force release, restart, commit, push, tag, package, publish, release, or deploy.
- Objective revision: `3`
- Objective SHA-256: `5969bb27060ea314566def0a366d2664d3ad49801c9c7d2abae318829a9388d1`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `9fb95ebeb5dbcfeee107227d194baf2f26c0ad5985b8ae02f61d000f36a3de15`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35870 | 2026-09-03T02:04:05.426Z | wave_replanned |  | PREFLIGHT | reason=W2 was recovered after a transport/runtime bootstrap outside its original synchronous execution. The runtime emitted RUNTIME_RESUME_REQUIRED and quiesced W2 at REPLAN with zero lease, mutation, proof, or checkpoint. Exact c213 preimages were reverified immediately before recovery. W3 changes the execution strategy from conflicting adopt_existing_files+patch to patch-only against those exact verified bytes, while preserving the same two-path scope and settled semantics. |
| 35871 | 2026-09-03T02:04:05.616Z | observation_span_recorded |  |  |  |
| 35872 | 2026-09-03T02:04:05.836Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35873 | 2026-09-03T02:04:06.037Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35874 | 2026-09-03T02:04:06.247Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 35875 | 2026-09-03T02:04:06.462Z | state_transition | READY | ROUTED | reason=route_selected |
| 35876 | 2026-09-03T02:04:06.691Z | observation_span_recorded |  |  |  |
| 35877 | 2026-09-03T02:04:07.752Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=893dd1888d424619b59de9ad07a278ba |
| 35878 | 2026-09-03T02:04:07.920Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35879 | 2026-09-03T02:04:08.781Z | patch_surface_observed |  |  |  |
| 35880 | 2026-09-03T02:04:08.953Z | observation_span_recorded |  |  |  |
| 35881 | 2026-09-03T02:04:09.221Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=893dd1888d424619b59de9ad07a278ba |
| 35882 | 2026-09-03T02:04:09.371Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35883 | 2026-09-03T02:04:10.165Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:044f5d92d303a4d9; input_fingerprint=7f31a260ba775a96d821ea829d67c4d768c813bd90af4485f4d200ce41550a2b |
| 35884 | 2026-09-03T02:04:10.548Z | managed_process_admitted |  |  | owner=default |
| 35885 | 2026-09-03T02:04:10.868Z | managed_process_started |  |  | owner=default |
| 35886 | 2026-09-03T02:04:12.318Z | managed_process_terminal |  |  | owner=default |
| 35887 | 2026-09-03T02:04:12.677Z | proof_recorded |  |  | stage_id=check:044f5d92d303a4d9; status=passed; cache_hit=False; input_fingerprint=7f31a260ba775a96d821ea829d67c4d768c813bd90af4485f4d200ce41550a2b |
| 35888 | 2026-09-03T02:04:12.886Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:90447173833573ac; input_fingerprint=55f9b7fd1bc63d84a399e4f21d31f48d622ea77c42d98eb5c40f77badc8e3ae5 |
| 35889 | 2026-09-03T02:04:13.273Z | managed_process_admitted |  |  | owner=default |
| 35890 | 2026-09-03T02:04:13.582Z | managed_process_started |  |  | owner=default |
| 35891 | 2026-09-03T02:04:56.185Z | managed_process_terminal |  |  | owner=default |
| 35892 | 2026-09-03T02:04:56.613Z | proof_recorded |  |  | stage_id=check:90447173833573ac; status=passed; cache_hit=False; input_fingerprint=55f9b7fd1bc63d84a399e4f21d31f48d622ea77c42d98eb5c40f77badc8e3ae5 |
| 35893 | 2026-09-03T02:04:56.793Z | proof_cache_miss |  |  | reason=cold; stage_id=check:35c457ea08a282c7; input_fingerprint=64e57798d5a506ba5abfe2ff4dee91d36d8a8a4385dde620b0ff24abce13a814 |
| 35894 | 2026-09-03T02:04:57.261Z | managed_process_admitted |  |  | owner=default |
| 35895 | 2026-09-03T02:04:57.901Z | managed_process_started |  |  | owner=default |
| 35896 | 2026-09-03T02:04:58.359Z | managed_process_terminal |  |  | owner=default |
| 35897 | 2026-09-03T02:04:58.679Z | proof_recorded |  |  | stage_id=check:35c457ea08a282c7; status=passed; cache_hit=False; input_fingerprint=64e57798d5a506ba5abfe2ff4dee91d36d8a8a4385dde620b0ff24abce13a814 |
| 35898 | 2026-09-03T02:04:59.683Z | observation_span_recorded |  |  |  |
| 35899 | 2026-09-03T02:04:59.866Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 35900 | 2026-09-03T02:05:26.118Z | managed_process_admitted |  |  | owner=default |
| 35901 | 2026-09-03T02:05:26.485Z | managed_process_started |  |  | owner=default |
| 35902 | 2026-09-03T02:05:26.975Z | managed_process_terminal |  |  | owner=default |
| 35903 | 2026-09-03T02:05:34.476Z | managed_process_admitted |  |  | owner=default |
| 35904 | 2026-09-03T02:05:35.068Z | managed_process_started |  |  | owner=default |
| 35905 | 2026-09-03T02:05:35.518Z | managed_process_terminal |  |  | owner=default |
| 35906 | 2026-09-03T02:07:53.905Z | quality_outcome_recorded |  |  |  |
| 35907 | 2026-09-03T02:07:54.086Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 35908 | 2026-09-03T02:07:54.383Z | observation_span_recorded |  |  |  |
| 35909 | 2026-09-03T02:07:54.649Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:044f5d92d303a4d9 | passed | 7f31a260ba775a96d821ea829d67c4d768c813bd90af4485f4d200ce41550a2b | False | 2180 | 0 |
| check:90447173833573ac | passed | 55f9b7fd1bc63d84a399e4f21d31f48d622ea77c42d98eb5c40f77badc8e3ae5 | False | 43329 | 0 |
| check:35c457ea08a282c7 | passed | 64e57798d5a506ba5abfe2ff4dee91d36d8a8a4385dde620b0ff24abce13a814 | False | 1502 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 6bc0ff33dd8440aa80631f53e4662341 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 7cd505c302ef467fecf1d076de8ca4d67a22d49c27fff06de69aaca67669b187 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `106`
- Chain head: `379005b6f4927cf124fc210388ababb4c878ae24f951c8efdee77d8497e744c7`
