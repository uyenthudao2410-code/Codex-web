# Orchestration Wave 1

- Run: `28bd721b83b34d67a76c039988c6e32c`
- Wave: `24e47493cd204408bc9e83c692cc3683`
- Objective: Fix paired_policy_evaluation measurement overhead without changing evaluation semantics. The real ledger scan over ~260 mostly-untagged runs exceeded 30 seconds because the evaluator materialized accepted_result_evaluation for every run before rejecting untagged history. Filter evaluation-tagged baseline/candidate rows in SQLite first, then materialize economics only for those rows. Preserve the bounded 500 tagged-row cap, report total ledger_run_count and tagged_runs_scanned truthfully, keep representative/source/oracle/quality/cost gates unchanged, and keep zero-pair behavior fail-closed. This is a localized measurement-performance bugfix only; do not change routing/review/provider behavior and do not call providers.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `704ea7dda83949fd962a55060ae33c9b1259de390d70bdb980625dfa8fa83e79`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4220 | 2026-08-15T04:32:51.835Z | run_started |  | PREFLIGHT |  |
| 4221 | 2026-08-15T04:32:52.008Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4222 | 2026-08-15T04:32:52.148Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4223 | 2026-08-15T04:32:52.290Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4224 | 2026-08-15T04:32:52.466Z | state_transition | READY | ROUTED | reason=route_selected |
| 4225 | 2026-08-15T04:32:53.101Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1b86f9c07ffc4886bf83e164384d029b |
| 4226 | 2026-08-15T04:32:53.292Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4227 | 2026-08-15T04:32:54.108Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1b86f9c07ffc4886bf83e164384d029b |
| 4228 | 2026-08-15T04:32:54.244Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4229 | 2026-08-15T04:32:54.701Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2b08e8f9a183efa0d5a80553f7d230c289a29ed96631c3b576fba1705252b43c |
| 4230 | 2026-08-15T04:32:58.261Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2b08e8f9a183efa0d5a80553f7d230c289a29ed96631c3b576fba1705252b43c |
| 4231 | 2026-08-15T04:32:58.789Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4232 | 2026-08-15T04:33:14.100Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 2b08e8f9a183efa0d5a80553f7d230c289a29ed96631c3b576fba1705252b43c | False | 3266 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bec22af4dbab41a0b6efed5bf16b5da5 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 151cd914a6da41d2a06b7b05eec17d8316563b97c70cac513b0fc9fba4487a40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `37c63f026d08c6fa407f8f56792a369ff6bde966613734fdc28f80b8f5d2ac02`
