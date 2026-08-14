# Orchestration Wave 2

- Run: `e8f33e572ca64c53a3b19d04aa673e17`
- Wave: `3b605ae688d346ae8bfb5dbf45b23c0d`
- Objective: Implement Wave 0 measurement-correctness improvements on top of the current concurrent dashboard without changing routing policy, public MCP tool count, or authority semantics. Add exact model_visible_bytes accounting for MCP text actually projected to the model; preserve request_bytes/response_bytes only as transport/payload telemetry, not token truth. Allow the orchestration ledger to persist only exact known non-secret numeric token-usage counters from model economics while continuing to redact API/auth/credential token fields and invalid/string values. Update the existing dashboard to estimate context-equivalent tokens only from model_visible_bytes, clearly label context estimates and SCENARIO costs, and prefer measured delegation economics token counts for model/lane rows when available, with MEASURED vs ESTIMATED evidence labels. Do not call provider billing APIs, do not add a ninth tool, do not alter cost/routing thresholds, and preserve all unrelated dirty workspace changes.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `5d5c96e130e5e7823c6f179bfb6b9795cad811b46f443cbbb1f45b27d86d3d02`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1623 | 2026-08-14T08:43:38.311Z | wave_replanned |  | PREFLIGHT | reason=The combined runtime+dashboard patch was rejected before mutation because a dashboard context hunk was ambiguous. Split the work so the runtime telemetry/security change is deterministic and independently testable. |
| 1624 | 2026-08-14T08:43:38.596Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1625 | 2026-08-14T08:43:38.813Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1626 | 2026-08-14T08:43:39.055Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1627 | 2026-08-14T08:43:39.298Z | state_transition | READY | ROUTED | reason=route_selected |
| 1628 | 2026-08-14T08:43:40.097Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8208fec87cab4787bfb2e235bf75b9d5 |
| 1629 | 2026-08-14T08:43:40.347Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1630 | 2026-08-14T08:43:41.781Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8208fec87cab4787bfb2e235bf75b9d5 |
| 1631 | 2026-08-14T08:43:42.014Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1632 | 2026-08-14T08:43:43.023Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1633 | 2026-08-14T08:46:17.088Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 34ed081e799540e38917e7cca7071401 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `054cbf1c266ae4e2c3d782ff18050c03ecc4a8adcbbe3d5272326d0f083516de`
