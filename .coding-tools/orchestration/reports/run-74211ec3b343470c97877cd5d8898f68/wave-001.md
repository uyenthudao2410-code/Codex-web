# Orchestration Wave 1

- Run: `74211ec3b343470c97877cd5d8898f68`
- Wave: `158966d4829443089f628fe50e2fa28c`
- Objective: P1.B1b proof repair: remove the incorrect source-level assertion that performance.now must appear literally in ChatViewController. Clock semantics intentionally live in the separately tested observer-script builder. Do not change production wiring. Re-run the focused Node evaluation/UI tests.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `1b0523b52a117a348b68339261fe5300a2944335d4f68fdc8d95de69ec5a6009`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4911 | 2026-08-15T08:10:29.594Z | run_started |  | PREFLIGHT |  |
| 4912 | 2026-08-15T08:10:30.250Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4913 | 2026-08-15T08:10:30.409Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4914 | 2026-08-15T08:10:30.593Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4915 | 2026-08-15T08:10:30.794Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4916 | 2026-08-15T08:10:30.950Z | state_transition | READY | ROUTED | reason=route_selected |
| 4917 | 2026-08-15T08:10:31.746Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c0a284c196db4ea9856028fa14e2d4c0 |
| 4918 | 2026-08-15T08:10:31.935Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4919 | 2026-08-15T08:10:32.696Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c0a284c196db4ea9856028fa14e2d4c0 |
| 4920 | 2026-08-15T08:10:32.900Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4921 | 2026-08-15T08:10:33.592Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=120be315e0797be67d9bdd77aae98d7b76786a13eb8ed2794ad379cfb3ac911f |
| 4922 | 2026-08-15T08:10:34.307Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=120be315e0797be67d9bdd77aae98d7b76786a13eb8ed2794ad379cfb3ac911f |
| 4923 | 2026-08-15T08:10:35.131Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4924 | 2026-08-15T08:10:48.603Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 120be315e0797be67d9bdd77aae98d7b76786a13eb8ed2794ad379cfb3ac911f | False | 405 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 3f3e0d3c1c3644e595ddb35047d99ead | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | d31ba0edff4af266dfc7ec9c6f64e08f06ceb0af6d409dd1c4f635a8fbd4f98a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `2265be74212bb76cdc299dd145229a53b4dd4581e8350a0880ef19564e8175b1`
