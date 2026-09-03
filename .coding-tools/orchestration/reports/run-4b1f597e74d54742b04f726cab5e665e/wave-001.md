# Orchestration Wave 1

- Run: `4b1f597e74d54742b04f726cab5e665e`
- Wave: `eb7ba8e957cf49f68a6ca12dcf0d8cd8`
- Objective: Fresh EOCL RUN/WAVE only; do not reuse or mutate any prior accepted-code activation intent. Residual bugfix: close the fail-closed persistence gap in RecoveryActionStore durable_epoch_binding. PRE-MUTATION HARD GATE: the two owned dirty files must exactly match accepted checkpoint c213617ecc4941ac907433e69bc64e6c receipts before any write: electron/services/recoveryActionStore.js sha256=0e857c5e7d3932bcbc08832e5d9fff4737db0d01c489dac3f06e208d0e661872 and tests/recovery-activation.test.js sha256=062e6653574e8be1966f26215f121843fdfcf64d57a870918c309cc7ade658c4. Use exact-byte adoption as the preimage gate and stop on mismatch. Own and mutate ONLY those two paths; acquire a write lease scoped to exactly those two paths; do not touch recoveryActivation.js or any other concurrent WIP.

Required semantics: (1) preserve the existing compatible three-field durable_epoch_binding shape across Recovery Host handoff; do not add required persisted fields. (2) At load/use time, durableEpochBinding must require safe created_at_unix_ms from the action record and reject a durable expiry beyond a deterministic persisted lifetime cap derived from action creation + MAX_DURABLE_EPOCH_TTL_MS + at most the authenticated request admission window of 60 seconds. Introduce an explicitly named constant for that admission allowance; cap must stay bounded and fail-closed. (3) bindDurableEpoch must enforce the same persisted cap in addition to its existing now-relative 10-minute check; preserve immutable request expires_at_unix_ms and exact operation/epoch validation. (4) Malformed, identity-mismatched, or over-bound stored binding is non-authoritative: replay/get/active fall back to request expiry and, once that expires, terminalize ACTIVATION_REQUEST_EXPIRED; never trust the tampered durable deadline. (5) Add focused regressions proving a valid existing three-field binding remains active after request expiry but before epoch expiry, and a tampered over-bound stored three-field binding is rejected as authority and expires on the original request deadline. Implement the smallest coherent patch.

Proof must run in this exact order after mutation: node --test tests/recovery-activation.test.js; then node --test tests/accepted-code-activation.test.js; then scoped git diff --check for the two owned paths. Produce exact-byte receipts/fingerprints, reach ACCEPTING, release/quiesce write resources, and STOP for ChatWeb Sol/user explicit acceptance. Do NOT self-accept or reject. No direct ledger/projection/runtime-state edits, force release, restart, commit, push, tag, package, publish, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `5969bb27060ea314566def0a366d2664d3ad49801c9c7d2abae318829a9388d1`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `9fb95ebeb5dbcfeee107227d194baf2f26c0ad5985b8ae02f61d000f36a3de15`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35804 | 2026-09-02T10:20:50.452Z | run_started |  | PREFLIGHT |  |
| 35805 | 2026-09-02T10:20:50.818Z | observation_span_recorded |  |  |  |
| 35806 | 2026-09-02T10:20:51.025Z | solution_shadow_recommended |  |  |  |
| 35807 | 2026-09-02T10:20:52.010Z | observation_span_recorded |  |  |  |
| 35808 | 2026-09-02T10:20:52.209Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35809 | 2026-09-02T10:20:52.422Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 35810 | 2026-09-02T10:20:52.624Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35811 | 2026-09-02T10:20:52.818Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35812 | 2026-09-02T10:20:52.987Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 35813 | 2026-09-02T10:20:53.180Z | state_transition | READY | ROUTED | reason=route_selected |
| 35814 | 2026-09-02T10:20:53.366Z | observation_span_recorded |  |  |  |
| 35815 | 2026-09-02T10:20:54.358Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0871c85dbe69480db494c3595cf1736e |
| 35816 | 2026-09-02T10:20:54.560Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35817 | 2026-09-02T10:20:55.650Z | existing_file_adoption_observed |  |  |  |
| 35818 | 2026-09-02T10:20:55.837Z | observation_span_recorded |  |  |  |
| 35819 | 2026-09-02T10:20:56.179Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0871c85dbe69480db494c3595cf1736e |
| 35820 | 2026-09-02T10:20:56.363Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35821 | 2026-09-02T10:20:57.524Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:044f5d92d303a4d9; input_fingerprint=28e8f7b9553bf9d90bd55edab24ae1653d58977d520bf7d05dd5695d20402cc9 |
| 35822 | 2026-09-02T10:20:57.994Z | managed_process_admitted |  |  | owner=default |
| 35823 | 2026-09-02T10:20:58.375Z | managed_process_started |  |  | owner=default |
| 35824 | 2026-09-02T10:21:00.118Z | managed_process_terminal |  |  | owner=default |
| 35825 | 2026-09-02T10:21:00.422Z | proof_recorded |  |  | stage_id=check:044f5d92d303a4d9; status=passed; cache_hit=False; input_fingerprint=28e8f7b9553bf9d90bd55edab24ae1653d58977d520bf7d05dd5695d20402cc9 |
| 35826 | 2026-09-02T10:21:00.590Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:90447173833573ac; input_fingerprint=da15aec8513e5999bdd9e320904acecd5e3d775396886977d68b00c23a15b6d3 |
| 35827 | 2026-09-02T10:21:00.989Z | managed_process_admitted |  |  | owner=default |
| 35828 | 2026-09-02T10:21:01.330Z | managed_process_started |  |  | owner=default |
| 35829 | 2026-09-02T10:21:52.514Z | managed_process_terminal |  |  | owner=default |
| 35830 | 2026-09-02T10:21:52.886Z | proof_recorded |  |  | stage_id=check:90447173833573ac; status=passed; cache_hit=False; input_fingerprint=da15aec8513e5999bdd9e320904acecd5e3d775396886977d68b00c23a15b6d3 |
| 35831 | 2026-09-02T10:21:53.092Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9d0053bdb151e714; input_fingerprint=9409596620b0df274162e59ebc654c3758a75d4dcce14b721256dd359c1eb160 |
| 35832 | 2026-09-02T10:21:53.521Z | managed_process_admitted |  |  | owner=default |
| 35833 | 2026-09-02T10:21:53.871Z | managed_process_started |  |  | owner=default |
| 35834 | 2026-09-02T10:21:54.381Z | managed_process_terminal |  |  | owner=default |
| 35835 | 2026-09-02T10:21:54.730Z | proof_recorded |  |  | stage_id=check:9d0053bdb151e714; status=passed; cache_hit=False; input_fingerprint=9409596620b0df274162e59ebc654c3758a75d4dcce14b721256dd359c1eb160 |
| 35836 | 2026-09-02T10:21:54.955Z | observation_span_recorded |  |  |  |
| 35837 | 2026-09-02T10:21:55.189Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 35838 | 2026-09-02T10:22:46.606Z | observation_span_recorded |  |  |  |
| 35839 | 2026-09-02T10:22:46.816Z | failure_observed | ACCEPTING | ACCEPTING | reason=REPLAN_REQUIRED_ZERO_DIFF_RESIDUAL_GAP_UNIMPLEMENTED: exact c213 preimages were adopted and all requested baseline proofs passed, but this wave produced affected_files=[] / modified_files=0, so it did not implement the required persisted durable-epoch cap. Preserve the fresh RUN and open a corrective wave with an explicit exact two-path patch; do not reuse proof from this zero-diff fingerprint as implementation proof.; failure_class=SOL_REJECTED |
| 35840 | 2026-09-02T10:22:46.869Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 35841 | 2026-09-02T10:22:47.026Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:044f5d92d303a4d9 | passed | 28e8f7b9553bf9d90bd55edab24ae1653d58977d520bf7d05dd5695d20402cc9 | False | 2525 | 0 |
| check:90447173833573ac | passed | da15aec8513e5999bdd9e320904acecd5e3d775396886977d68b00c23a15b6d3 | False | 51938 | 0 |
| check:9d0053bdb151e714 | passed | 9409596620b0df274162e59ebc654c3758a75d4dcce14b721256dd359c1eb160 | False | 1261 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `106`
- Chain head: `379005b6f4927cf124fc210388ababb4c878ae24f951c8efdee77d8497e744c7`
