# Orchestration Wave 1

- Run: `1cd4db2e927b45afb1356bdb1cc43ba5`
- Wave: `3917b24b7de2417f9111baeb779a8bc2`
- Objective: P1 accepted-run production sample after the handoff shadow A/B. Run the repository's canonical runtime activation/production telemetry benchmark on the current checkout and capture the current accepted-run TTA sample plus activation/idempotency/proof-cache counters. Do not modify source files. Treat mixed workload averages cautiously: report whether the benchmark exposes enough cohort dimensions (entry surface, route, task class, accepted/repair status) for apples-to-apples comparison. If not, mark cohort calibration as still pending rather than comparing raw global averages. Do not commit, push, restart, or deploy.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `e429d1b859fcfedf835cacce7421a4985d21950c37e7106c38aa33016310fe42`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 684 | 2026-08-14T02:23:20.711Z | run_started |  | PREFLIGHT |  |
| 685 | 2026-08-14T02:23:21.132Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 686 | 2026-08-14T02:23:21.282Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 687 | 2026-08-14T02:23:21.454Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 688 | 2026-08-14T02:23:21.601Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 689 | 2026-08-14T02:23:21.751Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 690 | 2026-08-14T02:23:21.932Z | state_transition | READY | ROUTED | reason=route_selected |
| 691 | 2026-08-14T02:23:22.446Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4fea089b8bf7417598230d9cb7cd99f3 |
| 692 | 2026-08-14T02:23:22.601Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 693 | 2026-08-14T02:23:23.114Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4fea089b8bf7417598230d9cb7cd99f3 |
| 694 | 2026-08-14T02:23:23.276Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 695 | 2026-08-14T02:23:24.979Z | proof_recorded |  |  | stage_id=check:d97ff2ecbaa79b27; status=passed; cache_hit=False; input_fingerprint=a344ff2d522e0c7544598f2e3ef90f8c3778fac0f247d40298ddfa7c96672b46 |
| 696 | 2026-08-14T02:23:25.184Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 697 | 2026-08-14T02:23:57.893Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d97ff2ecbaa79b27 | passed | a344ff2d522e0c7544598f2e3ef90f8c3778fac0f247d40298ddfa7c96672b46 | False | 1131 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 428fd4aac81e408ea7c7951fa463a2f4 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 38236db57c1ada9e8e1771e7a44c27d901bee006fdedb3c7ab54bbec3fc1d681 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `947906e8ee74dedd9705fa5153abb03d73faaa424e7996f435a2514cdbfd49a7`
