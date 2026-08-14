# Orchestration Wave 1

- Run: `e8f33e572ca64c53a3b19d04aa673e17`
- Wave: `5e3cac708d6a4660962b0bd6d558ee26`
- Objective: Implement Wave 0 measurement-correctness improvements on top of the current concurrent dashboard without changing routing policy, public MCP tool count, or authority semantics. Add exact model_visible_bytes accounting for MCP text actually projected to the model; preserve request_bytes/response_bytes only as transport/payload telemetry, not token truth. Allow the orchestration ledger to persist only exact known non-secret numeric token-usage counters from model economics while continuing to redact API/auth/credential token fields and invalid/string values. Update the existing dashboard to estimate context-equivalent tokens only from model_visible_bytes, clearly label context estimates and SCENARIO costs, and prefer measured delegation economics token counts for model/lane rows when available, with MEASURED vs ESTIMATED evidence labels. Do not call provider billing APIs, do not add a ninth tool, do not alter cost/routing thresholds, and preserve all unrelated dirty workspace changes.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `5d5c96e130e5e7823c6f179bfb6b9795cad811b46f443cbbb1f45b27d86d3d02`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1613 | 2026-08-14T08:43:03.452Z | run_started |  | PREFLIGHT |  |
| 1614 | 2026-08-14T08:43:03.656Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1615 | 2026-08-14T08:43:03.840Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1616 | 2026-08-14T08:43:04.038Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1617 | 2026-08-14T08:43:04.214Z | state_transition | READY | ROUTED | reason=route_selected |
| 1618 | 2026-08-14T08:43:04.870Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=06a7d34122c644a290652ea1fca45e72 |
| 1619 | 2026-08-14T08:43:05.048Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1620 | 2026-08-14T08:43:05.636Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1621 | 2026-08-14T08:43:06.062Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=06a7d34122c644a290652ea1fca45e72 |
| 1622 | 2026-08-14T08:43:06.255Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `21`
- Chain head: `054cbf1c266ae4e2c3d782ff18050c03ecc4a8adcbbe3d5272326d0f083516de`
