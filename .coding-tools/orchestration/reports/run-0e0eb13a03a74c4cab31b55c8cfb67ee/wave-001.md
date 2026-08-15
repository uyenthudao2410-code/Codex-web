# Orchestration Wave 1

- Run: `0e0eb13a03a74c4cab31b55c8cfb67ee`
- Wave: `3adb11eabb0744c7aadab9f485f96d3d`
- Objective: P0 test step 4b: update schema/runtime contract regressions for evaluation schema v2 and task_control quality, and update the expected smart-v3 contract SHA to the deterministic value produced by the new public schemas. No production code changes.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `f0494121710567479ed1a3c2e91d7ea8f925a9001c21250fffe359867b263e19`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4795 | 2026-08-15T07:46:23.980Z | run_started |  | PREFLIGHT |  |
| 4796 | 2026-08-15T07:46:24.687Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4797 | 2026-08-15T07:46:25.081Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4798 | 2026-08-15T07:46:25.320Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4799 | 2026-08-15T07:46:25.567Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4800 | 2026-08-15T07:46:25.768Z | state_transition | READY | ROUTED | reason=route_selected |
| 4801 | 2026-08-15T07:46:26.493Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3a6cd96b52d841b6b74be5dae2d4fc74 |
| 4802 | 2026-08-15T07:46:26.664Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4803 | 2026-08-15T07:46:27.803Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3a6cd96b52d841b6b74be5dae2d4fc74 |
| 4804 | 2026-08-15T07:46:28.025Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4805 | 2026-08-15T07:46:29.092Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4806 | 2026-08-15T07:46:39.041Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 955238a8c00049638621e3e6bad8676f | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `e167e2b32cca493e9c16d999bc7759d2255c7970590e6e22938ddaafe1ebfd0c`
