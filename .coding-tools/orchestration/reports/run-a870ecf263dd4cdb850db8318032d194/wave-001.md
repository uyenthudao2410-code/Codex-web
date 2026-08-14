# Orchestration Wave 1

- Run: `a870ecf263dd4cdb850db8318032d194`
- Wave: `b674afb3cb2f45f59947ec47bea37530`
- Objective: P3A semantic-safe required idempotency: close the first agent_workflow execute gap by using TaskState.task_id as the workflow operation epoch. Before auto-deriving a required agent_workflow execute key, validate the public schema, then ensure/reuse the current visible task epoch; preserve any nonterminal EOCL run even if TaskState status is unusual. Derive agent_workflow execute keys from operation + task_id + canonical request hash, not run/wave or transport request id. A completed/failed/stopped task with no live EOCL authority gets a new task epoch, so an intentionally new identical operation receives a different key. Keep task_control accept/reject run/wave + caller/fence semantics unchanged. Add end-to-end tests for initial auto-key, restart replay, same-task exact replay, and new task epoch allowing identical payload as a new operation.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `13350a87908d57923ff32916f82736eeef309578f44a45388343f485ead6f550`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3273 | 2026-08-14T18:10:30.679Z | run_started |  | PREFLIGHT |  |
| 3274 | 2026-08-14T18:10:30.811Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3275 | 2026-08-14T18:10:30.977Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3276 | 2026-08-14T18:10:31.102Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3277 | 2026-08-14T18:10:31.232Z | state_transition | READY | ROUTED | reason=route_selected |
| 3278 | 2026-08-14T18:10:31.760Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cdd30a1633de4428804e1b869b7d9d63 |
| 3279 | 2026-08-14T18:10:31.891Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3280 | 2026-08-14T18:10:32.476Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cdd30a1633de4428804e1b869b7d9d63 |
| 3281 | 2026-08-14T18:10:32.612Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3282 | 2026-08-14T18:10:33.014Z | proof_cache_miss |  |  | reason=cold; stage_id=check:56029c100af28fc0; input_fingerprint=4289939a9f280af99580f1f2087585dffa240fff95c179f8a89b73a117236fc8 |
| 3283 | 2026-08-14T18:10:34.669Z | proof_recorded |  |  | stage_id=check:56029c100af28fc0; status=failed; cache_hit=False; input_fingerprint=4289939a9f280af99580f1f2087585dffa240fff95c179f8a89b73a117236fc8 |
| 3284 | 2026-08-14T18:10:34.806Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 3285 | 2026-08-14T18:10:34.918Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:56029c100af28fc0 | failed | 4289939a9f280af99580f1f2087585dffa240fff95c179f8a89b73a117236fc8 | False | 1332 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `d7fdaa5a3b5d6391d44ab5fb4ea120e33998895cbd0639751db9ab89a787cbad`
