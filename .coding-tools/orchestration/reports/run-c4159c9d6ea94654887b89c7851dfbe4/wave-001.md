# Orchestration Wave 1

- Run: `c4159c9d6ea94654887b89c7851dfbe4`
- Wave: `fbea61a1ca4e4df498e62f1235b4f5f9`
- Objective: Prepare R3B production wiring only; do not modify files or run implementation/proof commands. Inspect the verified current R3A source_snapshot contract/module and the exact current R2B structured validation path. Identify current symbol names and the minimal edits to: add an internal synchronous source-snapshot capture request with explicit capability gate; capture bounded dirty source at a full base HEAD; carry only the validated snapshot payload transiently on the start_validation_job request while retaining only base-head + snapshot digest in durable/public validation metadata; make snapshot-aware placement require the new capability and permit a dirty primary checkout because execution materializes a private clone; choose a distinct server_compute target when eligible, otherwise execute the same snapshot on the source Runner; materialize the snapshot in the Runner before validation and redirect cwd to the private clone plus project-relative cwd; keep the materialization RAII owner alive through terminal/stop then cleanup; and preserve the existing clean R2B path unchanged. Fail closed for old runners, oversize/malformed snapshot, source capture drift, target capability loss, target base-head mismatch, materialization failure, and outcome-unknown. No public MCP tool, no auto Git commit, no git worktree, no authoritative checkout write, no raw snapshot contents in job/status/inventory. Determine exact tests that can prove production wiring without running root monolithic cargo test; prefer core placement/protocol tests + runner focused tests + compile of root tests, and if a small existing server test target is available use it. Return one concrete change set.
- Mode: `mcp_only`
- Base HEAD: `6b5d16e980058d51585f039eff918d938bbb66e9`
- Worktree fingerprint: `3ffbaff0e9a4276159f7515f2a3e0e862fe05de8a9d642a0a0e580e5e821fb06`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8838 | 2026-08-16T14:50:49.617Z | run_started |  | PREFLIGHT |  |
| 8839 | 2026-08-16T14:50:58.814Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8840 | 2026-08-16T15:00:21.580Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8841 | 2026-08-16T15:00:21.705Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8842 | 2026-08-16T15:00:21.860Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8843 | 2026-08-16T15:00:21.998Z | state_transition | READY | ROUTED | reason=route_selected |
| 8844 | 2026-08-16T15:00:22.410Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=edfcaa5db910433a9167999b10cdc298 |
| 8845 | 2026-08-16T15:00:22.510Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8846 | 2026-08-16T15:00:23.235Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=edfcaa5db910433a9167999b10cdc298 |
| 8847 | 2026-08-16T15:00:23.361Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8848 | 2026-08-16T15:00:23.738Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=46083365c09fb2e2d9911e3c1106126582194d4c60d80eae4c1f2bae3c22b4ce |
| 8849 | 2026-08-16T15:00:24.027Z | managed_process_admitted |  |  | owner=default |
| 8850 | 2026-08-16T15:00:24.361Z | managed_process_started |  |  | owner=default |
| 8851 | 2026-08-16T15:00:30.078Z | managed_process_terminal |  |  | owner=default |
| 8852 | 2026-08-16T15:00:30.326Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=failed; cache_hit=False; input_fingerprint=46083365c09fb2e2d9911e3c1106126582194d4c60d80eae4c1f2bae3c22b4ce |
| 8853 | 2026-08-16T15:00:30.451Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8854 | 2026-08-16T15:00:30.544Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8855 | 2026-08-16T15:00:30.679Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | failed | 46083365c09fb2e2d9911e3c1106126582194d4c60d80eae4c1f2bae3c22b4ce | False | 6335 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `fa3d5c9513ac34e06a5f218e6d7d0fab31e3a73b2babcf748a70859fce76e1c4`
