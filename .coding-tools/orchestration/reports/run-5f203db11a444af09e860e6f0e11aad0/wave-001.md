# Orchestration Wave 1

- Run: `5f203db11a444af09e860e6f0e11aad0`
- Wave: `6a4024514dd340aab8da9ad37402ebb2`
- Objective: P0 step 3b: make paired_policy_evaluation fail closed unless both policies share complete causal identity (base/worktree/contract/task/oracle/environment/tool/evaluation schema/runtime/cache), expose identity mismatch reasons, rename candidate-credit comparison to external_candidate_credit_delta with explicit non-total-cost semantics, and require critical-defect evidence for paired ROI review. Preserve all routing defaults; no restart/commit/push/models/synthetic workload.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `a152d14a82d064b843730022b3b9c420e297511f6e68f63b393b38ea5ce41590`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4756 | 2026-08-15T07:43:29.047Z | run_started |  | PREFLIGHT |  |
| 4757 | 2026-08-15T07:43:29.605Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4758 | 2026-08-15T07:43:29.786Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4759 | 2026-08-15T07:43:29.961Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4760 | 2026-08-15T07:43:30.197Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4761 | 2026-08-15T07:43:30.460Z | state_transition | READY | ROUTED | reason=route_selected |
| 4762 | 2026-08-15T07:43:31.257Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4f1cc7ca05ac4eb3bc3a1d9e21865c18 |
| 4763 | 2026-08-15T07:43:31.768Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4764 | 2026-08-15T07:43:32.978Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4f1cc7ca05ac4eb3bc3a1d9e21865c18 |
| 4765 | 2026-08-15T07:43:33.185Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4766 | 2026-08-15T07:43:34.403Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4767 | 2026-08-15T07:43:48.017Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1082523be0de4650b5338ce2be51ee60 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `f632abd4bc89b6d1f6890c1ad3d5d2be4b734ffcf2a76c9638d7f33058acb7dd`
