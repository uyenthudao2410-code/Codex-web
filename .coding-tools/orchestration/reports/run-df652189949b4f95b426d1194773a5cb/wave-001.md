# Orchestration Wave 1

- Run: `df652189949b4f95b426d1194773a5cb`
- Wave: `9cdef606eecb43f3bbb71edf410b75ee`
- Objective: Repair FE0 operator completion-report projection contamination without changing routing or P4 policy. The accepted current task projection can have orchestration.run_id for one run while completion_report.source_run_wave.run_id is replaced by a different run after read-only audit/get activity. Preserve the existing frozen-schema operator_report_ack_v1 update extension and its exact-id fail-closed semantics. Make completion-report persistence ownership-safe: read-only inspection/audit of an explicit non-current run may return that run's report in the response but must not replace the current task's pending completion_report. Any persisted pending completion report must belong to the current task-projected orchestration run/wave. Add focused regressions covering cross-run audit non-contamination, exact report ACK success, stale/wrong ID rejection, and ability to start the next task only after ACK. No restart, commit, push, routing changes, tool-count changes, or P5 activation in this run.
- Mode: `mcp_only`
- Base HEAD: `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02`
- Worktree fingerprint: `6280e3070c6a4fca0017e0ed52dd39fb0d87678f10fadfb3cdd9839ef6f9da9a`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21616 | 2026-08-19T10:57:29.876Z | run_started |  | PREFLIGHT |  |
| 21617 | 2026-08-19T10:57:30.571Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21618 | 2026-08-19T10:58:32.703Z | solution_shadow_recommended |  |  |  |
| 21619 | 2026-08-19T10:59:49.087Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21620 | 2026-08-19T10:59:49.307Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21621 | 2026-08-19T10:59:49.468Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21622 | 2026-08-19T10:59:49.651Z | state_transition | READY | ROUTED | reason=route_selected |
| 21623 | 2026-08-19T10:59:50.117Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4dfcd7c7723640fb951743e11327c4a3 |
| 21624 | 2026-08-19T10:59:50.293Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21625 | 2026-08-19T10:59:50.867Z | patch_surface_observed |  |  |  |
| 21626 | 2026-08-19T10:59:51.123Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4dfcd7c7723640fb951743e11327c4a3 |
| 21627 | 2026-08-19T10:59:51.301Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21628 | 2026-08-19T10:59:51.634Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=6ae0cfeec1a8f49cff66a16024f0a032c2c37dbe1fb35ec4488b712b009ef7bb |
| 21629 | 2026-08-19T10:59:51.960Z | managed_process_admitted |  |  | owner=default |
| 21630 | 2026-08-19T10:59:52.218Z | managed_process_started |  |  | owner=default |
| 21631 | 2026-08-19T10:59:52.982Z | managed_process_terminal |  |  | owner=default |
| 21632 | 2026-08-19T10:59:53.293Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=6ae0cfeec1a8f49cff66a16024f0a032c2c37dbe1fb35ec4488b712b009ef7bb |
| 21633 | 2026-08-19T10:59:53.450Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e6e42d35e9561a72013f79e99a692af3072aa6b6d6197604a058d2f2cb874107 |
| 21634 | 2026-08-19T10:59:53.851Z | managed_process_admitted |  |  | owner=default |
| 21635 | 2026-08-19T10:59:54.160Z | managed_process_started |  |  | owner=default |
| 21636 | 2026-08-19T11:00:02.144Z | managed_process_terminal |  |  | owner=default |
| 21637 | 2026-08-19T11:00:02.484Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=e6e42d35e9561a72013f79e99a692af3072aa6b6d6197604a058d2f2cb874107 |
| 21638 | 2026-08-19T11:00:02.978Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21639 | 2026-08-19T11:00:26.690Z | quality_outcome_recorded |  |  |  |
| 21640 | 2026-08-19T11:00:26.892Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21641 | 2026-08-19T11:00:27.199Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:466c2f308b48c766 | passed | 6ae0cfeec1a8f49cff66a16024f0a032c2c37dbe1fb35ec4488b712b009ef7bb | False | 1340 | 0 |
| verify:tests | passed | e6e42d35e9561a72013f79e99a692af3072aa6b6d6197604a058d2f2cb874107 | False | 8641 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 217a131f61eb4678811b9c7454e330c9 | accepted | 17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02 | 7dc5c0bc0abe9bd30a3f9865b999c902dd9d1193e6273b38f0a486a7f9834964 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `c520b0257b4bba76fd006648ef88fcb4197281321b5c23edd0571f643a1d529f`
