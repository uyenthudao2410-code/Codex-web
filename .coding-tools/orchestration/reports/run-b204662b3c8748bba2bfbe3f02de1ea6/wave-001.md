# Orchestration Wave 1

- Run: `b204662b3c8748bba2bfbe3f02de1ea6`
- Wave: `2165d6ccafb94ef4b5ce05ee6984b18d`
- Objective: S4/W5 paired-evaluation gate, proof-only and no source/docs mutation. Use the repository's existing compare_route_policies.py CLI against the real current .coding-tools/orchestration/ledger.sqlite3. Baseline policy is chatweb_mcp (current preparation flow); candidate policy is context_compiler_shadow (new compiler treatment). Require min_pairs=10 and min_task_classes=4 to match the maintained W5 representative strata. Do not create synthetic/benchmark/replay tasks and do not mutate the ledger to manufacture pairs. Also prove the evaluator's zero-pair and missing-total-cost fail-closed behavior with existing focused tests. If the real ledger lacks complete comparable representative pairs, the accepted stage decision must be KEEP_SHADOW / NO_PROMOTION and auto-injection remains unavailable. No S5.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `57f858926cd17c4b91af585daef9d87caf2e539294a3f976e3565aeaec435c81`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24809 | 2026-08-21T00:16:45.697Z | run_started |  | PREFLIGHT |  |
| 24810 | 2026-08-21T00:16:45.996Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24811 | 2026-08-21T00:16:46.168Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24812 | 2026-08-21T00:16:46.413Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 24813 | 2026-08-21T00:16:46.613Z | state_transition | READY | ROUTED | reason=route_selected |
| 24814 | 2026-08-21T00:16:47.128Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b7e83461c1bc4e789cddf528cfa07aed |
| 24815 | 2026-08-21T00:16:47.279Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24816 | 2026-08-21T00:16:47.700Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b7e83461c1bc4e789cddf528cfa07aed |
| 24817 | 2026-08-21T00:16:47.913Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24818 | 2026-08-21T00:16:48.213Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4c19dfaa495126c1; input_fingerprint=a2bde9f988a5351478c28d692d958f7fa3adff8b7e42ff4948f28b6cc0d114e2 |
| 24819 | 2026-08-21T00:16:48.558Z | managed_process_admitted |  |  | owner=default |
| 24820 | 2026-08-21T00:16:48.850Z | managed_process_started |  |  | owner=default |
| 24821 | 2026-08-21T00:16:49.263Z | managed_process_terminal |  |  | owner=default |
| 24822 | 2026-08-21T00:16:49.700Z | proof_recorded |  |  | stage_id=check:4c19dfaa495126c1; status=passed; cache_hit=False; input_fingerprint=a2bde9f988a5351478c28d692d958f7fa3adff8b7e42ff4948f28b6cc0d114e2 |
| 24823 | 2026-08-21T00:16:49.900Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3a31543d42c8c52d; input_fingerprint=0f361c3971c94ef700b1df6a66466ae5c709584ec4a3d4092ec09497d8141af2 |
| 24824 | 2026-08-21T00:16:50.276Z | managed_process_admitted |  |  | owner=default |
| 24825 | 2026-08-21T00:16:50.600Z | managed_process_started |  |  | owner=default |
| 24826 | 2026-08-21T00:16:51.000Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 24827 | 2026-08-21T00:16:51.350Z | proof_recorded |  |  | stage_id=check:3a31543d42c8c52d; status=passed; cache_hit=False; input_fingerprint=0f361c3971c94ef700b1df6a66466ae5c709584ec4a3d4092ec09497d8141af2 |
| 24828 | 2026-08-21T00:16:51.584Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c427efed6cc6a4a6; input_fingerprint=f3df5ea9e98587eda5ea5b2a6f8bf45d48d4a0ccf3fd7949f967505c49422e3a |
| 24829 | 2026-08-21T00:16:52.021Z | managed_process_admitted |  |  | owner=default |
| 24830 | 2026-08-21T00:16:52.380Z | managed_process_started |  |  | owner=default |
| 24831 | 2026-08-21T00:16:52.800Z | managed_process_terminal |  |  | owner=default |
| 24832 | 2026-08-21T00:16:53.150Z | proof_recorded |  |  | stage_id=check:c427efed6cc6a4a6; status=passed; cache_hit=False; input_fingerprint=f3df5ea9e98587eda5ea5b2a6f8bf45d48d4a0ccf3fd7949f967505c49422e3a |
| 24833 | 2026-08-21T00:16:53.417Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 24834 | 2026-08-21T00:17:58.129Z | quality_outcome_recorded |  |  |  |
| 24835 | 2026-08-21T00:17:58.420Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 24836 | 2026-08-21T00:17:58.819Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4c19dfaa495126c1 | passed | a2bde9f988a5351478c28d692d958f7fa3adff8b7e42ff4948f28b6cc0d114e2 | False | 1103 | 0 |
| check:3a31543d42c8c52d | passed | 0f361c3971c94ef700b1df6a66466ae5c709584ec4a3d4092ec09497d8141af2 | False | 887 | 0 |
| check:c427efed6cc6a4a6 | passed | f3df5ea9e98587eda5ea5b2a6f8bf45d48d4a0ccf3fd7949f967505c49422e3a | False | 1233 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 9cd2827246e94720b12b95f8048a40c4 | accepted | 640ad37e3e571a0a56af376e9d3bda2b89bf0669 | 7ac923d94f71d76598b6b7bbcaf0593fd5004019ccaffec5806ae3e954494827 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `59c92edd2f339e4fda7505fdee040e04dd88cd1f5687ed01988eea133a72a402`
