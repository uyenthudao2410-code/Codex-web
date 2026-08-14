# Orchestration Wave 1

- Run: `6898afecdcd24b2999d3fed05151f579`
- Wave: `950cecefa99d49629bc73d6057a3fe57`
- Objective: Fix orchestration ledger lifecycle leakage when the single workspace task is stopped, cleared, or replaced. Add a helper that looks only at the current task state's exact orchestration.run_id, snapshots that exact run, and transitions it to ABORTED if it is nonterminal. Never use current_active_run fallback and never touch an unrelated run. Apply the helper before task_control stop, clear, and start replacement; pause must remain resumable and must not abort. Preserve existing command-kill behavior. Project ABORTED back into task state for stop. If the projected run is missing, do not invent another run. If an exact nonterminal run cannot legally abort, fail closed with a typed runtime error rather than silently leaving it active. Add focused tests proving stop/clear/replacement abort only the linked run, pause keeps it active, and an unrelated active run is untouched.
- Mode: `mcp_only`
- Base HEAD: `5f756b5f9a4ab29ca84401314bcc72efc17ae31b`
- Worktree fingerprint: `c1da2bdbf48179f8b65510f3ae14aaf39bfd0b3eda599c5d2cbe59f26babbe5b`
- Contract fingerprint: `ef20dd7909a9d4f33c717e9ea9ad4e03848f0b3e0634e374f4c35b13b387d6d4`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 885 | 2026-08-14T04:18:01.750Z | run_started |  | PREFLIGHT |  |
| 886 | 2026-08-14T04:18:01.938Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 887 | 2026-08-14T04:18:02.126Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 888 | 2026-08-14T04:18:02.317Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 889 | 2026-08-14T04:18:02.524Z | state_transition | READY | ROUTED | reason=route_selected |
| 890 | 2026-08-14T04:18:03.064Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cb2d6839fc594cdca17742217a6d28d3 |
| 891 | 2026-08-14T04:18:03.265Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 892 | 2026-08-14T04:18:03.899Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cb2d6839fc594cdca17742217a6d28d3 |
| 893 | 2026-08-14T04:18:04.074Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 894 | 2026-08-14T04:18:07.401Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=4e0b4e994f3ceded0c1799a67ce56882dc25e9e90d57fdd32d6408711770b0d7 |
| 895 | 2026-08-14T04:18:07.751Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 896 | 2026-08-14T04:18:29.862Z | state_transition | ACCEPTING | CHECKPOINTED | reason=chatweb_sol_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 4e0b4e994f3ceded0c1799a67ce56882dc25e9e90d57fdd32d6408711770b0d7 | False | 2750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 964aa104b13a49e99b4637d27669db72 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | 64f01f10534072e40c7781a37b496b88ef8a3aa25e1584415cad424d970d0f61 | ChatWeb Sol |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `4252fe30853f6031f985bd2c087ca802bbf28ddbe51d6183d235b1ba4e741f9d`
