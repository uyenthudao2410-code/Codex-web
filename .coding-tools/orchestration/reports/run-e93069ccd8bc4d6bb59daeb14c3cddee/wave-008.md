# Orchestration Wave 8

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Wave: `23672f6af4394df49b6a5204d8d76269`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Mode: `mcp_only`
- Base HEAD: `28a5f62f3f01d3a78d851beffd9a2c6a72f8302a`
- Worktree fingerprint: `438c744de3f8cf93538584ff7064ed521595a3236d829e7fd890e3b1b213e0ea`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24089 | 2026-08-20T12:45:42.424Z | wave_replanned |  | PREFLIGHT | reason=Changed evidence from proof ce12357a: compilation succeeds and all four required exact regressions pass; the sole remaining failure is rustfmt drift in model_result_projection.rs. Strategy changes from code repair to formatting-only normalization followed by full fingerprint-fresh proof. |
| 24090 | 2026-08-20T12:45:42.564Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24091 | 2026-08-20T12:45:42.724Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24092 | 2026-08-20T12:45:42.881Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 24093 | 2026-08-20T12:45:43.047Z | state_transition | READY | ROUTED | reason=route_selected |
| 24094 | 2026-08-20T12:45:43.490Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=77fd789617324e48bf7755f6b1f02e2a |
| 24095 | 2026-08-20T12:45:43.723Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24096 | 2026-08-20T12:45:44.165Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=77fd789617324e48bf7755f6b1f02e2a |
| 24097 | 2026-08-20T12:45:44.352Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24098 | 2026-08-20T12:45:44.754Z | proof_cache_miss |  |  | reason=cold; stage_id=check:866ef07f411ea748; input_fingerprint=863301997abe8ec157dc307a3041bf83a531f978206bcd695fd8052982ae5623 |
| 24099 | 2026-08-20T12:45:45.232Z | managed_process_admitted |  |  | owner=default |
| 24100 | 2026-08-20T12:45:45.535Z | managed_process_started |  |  | owner=default |
| 24101 | 2026-08-20T12:45:48.448Z | managed_process_terminal |  |  | owner=default |
| 24102 | 2026-08-20T12:45:48.768Z | proof_recorded |  |  | stage_id=check:866ef07f411ea748; status=passed; cache_hit=False; input_fingerprint=863301997abe8ec157dc307a3041bf83a531f978206bcd695fd8052982ae5623 |
| 24103 | 2026-08-20T12:45:48.975Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=93d33db02cb86e6e391e089a0e6bf50497f82a3013bd95db83d4a91c93622554 |
| 24104 | 2026-08-20T12:45:49.374Z | managed_process_admitted |  |  | owner=default |
| 24105 | 2026-08-20T12:45:49.632Z | managed_process_started |  |  | owner=default |
| 24106 | 2026-08-20T12:46:24.697Z | managed_process_terminal |  |  | owner=default |
| 24107 | 2026-08-20T12:46:25.548Z | managed_process_admitted |  |  | owner=default |
| 24108 | 2026-08-20T12:46:26.447Z | managed_process_started |  |  | owner=default |
| 24109 | 2026-08-20T12:47:30.228Z | managed_process_terminal |  |  | owner=default |
| 24110 | 2026-08-20T12:47:31.661Z | proof_recorded |  |  | stage_id=verify:all; status=passed; cache_hit=False; input_fingerprint=93d33db02cb86e6e391e089a0e6bf50497f82a3013bd95db83d4a91c93622554 |
| 24111 | 2026-08-20T12:47:31.980Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 24112 | 2026-08-20T12:50:14.528Z | quality_outcome_recorded |  |  |  |
| 24113 | 2026-08-20T12:50:14.756Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 24114 | 2026-08-20T12:50:15.166Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:866ef07f411ea748 | passed | 863301997abe8ec157dc307a3041bf83a531f978206bcd695fd8052982ae5623 | False | 3685 | 0 |
| verify:all | passed | 93d33db02cb86e6e391e089a0e6bf50497f82a3013bd95db83d4a91c93622554 | False | 102000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b3432eec3c9b4ee69793734d8a4a630f | accepted | 28a5f62f3f01d3a78d851beffd9a2c6a72f8302a | abf0a8f7f280c138070d0ab3d53e6907f6ad8fd96a3fe399d8a64356dab1de6d | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `70c3bcfdbbd73c573e8d80a46a4d343ba287a3d1bb6522d41ae64011a48c311c`
