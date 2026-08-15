# Orchestration Wave 1

- Run: `edd43e17f28a4a6eaf96b3ec5109ff5e`
- Wave: `d3fcfa1371544db3adf687c926da2063`
- Objective: Close the controlled-replay causal-acceptance gap without adding a public tool or inferring success from process exit code. After each isolated trial command, read that trial workspace's authoritative EOCL orchestration ledger and attest exactly one accepted run whose evaluation/source identity matches the trial manifest. Require an accepted checkpoint plus proof/oracle evidence, and fail closed on missing, ambiguous, identity-mismatched, or route-policy-mismatched evidence. Preserve existing plan-only and no-ledger behavior.
- Mode: `mcp_only`
- Base HEAD: `f64abe25a85e6abaa9fe9eeacd3665eb29a82515`
- Worktree fingerprint: `f6af1768139f11c1d9e716556a1876d781de9287fe376ce63e1a0ada40856556`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5303 | 2026-08-15T10:59:03.808Z | run_started |  | PREFLIGHT |  |
| 5304 | 2026-08-15T10:59:04.016Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5305 | 2026-08-15T10:59:04.208Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5306 | 2026-08-15T10:59:04.413Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5307 | 2026-08-15T10:59:04.593Z | state_transition | READY | ROUTED | reason=route_selected |
| 5308 | 2026-08-15T10:59:05.143Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bfb034cc19ce42e2b135f94e96913153 |
| 5309 | 2026-08-15T10:59:05.311Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5310 | 2026-08-15T10:59:05.943Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bfb034cc19ce42e2b135f94e96913153 |
| 5311 | 2026-08-15T10:59:06.147Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5312 | 2026-08-15T10:59:06.564Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=939b8229f883fde8edb360733fae5b5b3f1be313ed2b87650de54481366387ce |
| 5313 | 2026-08-15T10:59:25.610Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=939b8229f883fde8edb360733fae5b5b3f1be313ed2b87650de54481366387ce |
| 5314 | 2026-08-15T10:59:26.598Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5315 | 2026-08-15T11:00:07.211Z | failure_observed | ACCEPTING | ACCEPTING | reason=Focused tests pass, but acceptance review found one fail-closed gap: each accepted trial is individually attested, yet the executor does not verify that both policies in a pair have the same EOCL pair_fingerprint/worktree identity. A caller command could mutate source before EOCL run creation and still yield individually accepted evidence. Add pair-level fingerprint equality before declaring accepted_result_evidence_complete.; failure_class=SOL_REJECTED |
| 5316 | 2026-08-15T11:00:07.468Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 939b8229f883fde8edb360733fae5b5b3f1be313ed2b87650de54481366387ce | False | 18593 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `09bd841cd548ef4572bdf28648655b8d06706288e630c26cd721057845fc55c0`
