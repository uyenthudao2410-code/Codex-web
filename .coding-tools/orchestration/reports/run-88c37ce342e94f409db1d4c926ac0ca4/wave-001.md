# Orchestration Wave 1

- Run: `88c37ce342e94f409db1d4c926ac0ca4`
- Wave: `420d4d2c647a408284a453a227b325d1`
- Objective: Unblock apples-to-apples accepted-run routing analysis with the smallest historical-compatible telemetry change. Extend the standalone runtime activation benchmark to schema v2 and derive durable accepted-run cohorts without any SQLite schema migration. Cohort dimensions: entry_surface, route, task_class, acceptance_status, repair_status. Derive entry_surface='agent_workflow' only when existing run metadata contains both workflow and phase; otherwise 'unknown'. Derive task_class from metadata.task_class or metadata.workflow, route from the latest durable route_selected event, and repair_status='repaired' when any wave for the run is replanned, otherwise 'first_pass'. Keep the existing global accepted_run_tta. Add accepted_run_cohort_coverage and a deterministic accepted_run_cohorts list with n/p50/p90. Never invent missing dimensions. Add focused tests for complete first-pass cohort, repaired/latest-route cohort, and unknown fallback. Do not modify database schema or runtime orchestration semantics.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `52dd93f12d941a81129f4d1a246cd7e0297333d209db6770ddcc010238faa3e6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 700 | 2026-08-14T02:26:47.844Z | run_started |  | PREFLIGHT |  |
| 701 | 2026-08-14T02:26:48.007Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 702 | 2026-08-14T02:26:48.180Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 703 | 2026-08-14T02:26:48.364Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 704 | 2026-08-14T02:26:48.538Z | state_transition | READY | ROUTED | reason=route_selected |
| 705 | 2026-08-14T02:26:49.047Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3d3a86ac217c4cb5b737f6562a6c4e86 |
| 706 | 2026-08-14T02:26:49.228Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 707 | 2026-08-14T02:26:49.814Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3d3a86ac217c4cb5b737f6562a6c4e86 |
| 708 | 2026-08-14T02:26:49.978Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 709 | 2026-08-14T02:26:52.686Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=879c7e2639ecbc86e6f6ca2fafd902ff6a0ec4ec9e35f3b04f311e20315d6b6a |
| 710 | 2026-08-14T02:26:53.040Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 711 | 2026-08-14T02:27:07.571Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 879c7e2639ecbc86e6f6ca2fafd902ff6a0ec4ec9e35f3b04f311e20315d6b6a | False | 1969 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| afe88732ff0e44d0adff2ee5382a7b41 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 297a31300fedd9d4e9a99772c1cef7c68ca7d646f5a36ea39229144e4abc04f2 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `e6a3806dfcc7349e61557e928acd6aab19a19f2192bcbdd57f250dae6f2ff553`
