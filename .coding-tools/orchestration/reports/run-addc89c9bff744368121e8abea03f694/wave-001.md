# Orchestration Wave 1

- Run: `addc89c9bff744368121e8abea03f694`
- Wave: `e28e613ded424c2b8f2d61e3c8343754`
- Objective: P0 test step 4a: update orchestration-ledger evaluation fixtures for complete causal identity and add regressions for worktree drift rejection, delayed quality outcome projection/promotion gating, and external candidate-credit semantics. No production code changes in this wave.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `58e23cb3137ed277ca2fafb9a8b87de92f4d890df487e3696ee00097ade6781f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4783 | 2026-08-15T07:45:52.301Z | run_started |  | PREFLIGHT |  |
| 4784 | 2026-08-15T07:45:53.087Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4785 | 2026-08-15T07:45:53.308Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4786 | 2026-08-15T07:45:53.506Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4787 | 2026-08-15T07:45:53.797Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4788 | 2026-08-15T07:45:54.000Z | state_transition | READY | ROUTED | reason=route_selected |
| 4789 | 2026-08-15T07:45:54.658Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=30facde2ed00489790a946d3b790f23f |
| 4790 | 2026-08-15T07:45:55.024Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4791 | 2026-08-15T07:45:55.766Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=30facde2ed00489790a946d3b790f23f |
| 4792 | 2026-08-15T07:45:55.950Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4793 | 2026-08-15T07:45:57.311Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4794 | 2026-08-15T07:46:07.758Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d19dafd0877e46618fcae21bb56c43b7 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `0c2b42ddaeaf0d55086860adcf4713e052002033b757db30299dcc3115342fa6`
