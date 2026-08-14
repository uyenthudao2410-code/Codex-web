# Orchestration Wave 1

- Run: `200332da9f66499f8ff36e42c0d93005`
- Wave: `748b42ed5aae4ac7a035f445357acd0e`
- Objective: Fix the Execution Control Center analytics projection and evidence semantics without changing layout, routing policy, or the public MCP contract. The dashboard must consume PerformanceTraceStore.recent (legacy records fallback only), derive context-token equivalents only from measured model_visible_bytes, never from request/response transport bytes, and prefer measured numeric delegation economics for model rows. Clearly mark MEASURED vs ESTIMATED and SCENARIO cost. Preserve all concurrent UI work.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `2467f86778778423c80bfecf7018a939e6c0d28cf92f2aa16721614f594428bb`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1634 | 2026-08-14T08:46:56.446Z | run_started |  | PREFLIGHT |  |
| 1635 | 2026-08-14T08:46:57.079Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1636 | 2026-08-14T08:46:57.244Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1637 | 2026-08-14T08:46:57.444Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1638 | 2026-08-14T08:46:57.698Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1639 | 2026-08-14T08:46:57.903Z | state_transition | READY | ROUTED | reason=route_selected |
| 1640 | 2026-08-14T08:46:58.629Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=00816b6caf07426b808c638387206b43 |
| 1641 | 2026-08-14T08:46:58.911Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1642 | 2026-08-14T08:46:59.426Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1643 | 2026-08-14T08:46:59.754Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=00816b6caf07426b808c638387206b43 |
| 1644 | 2026-08-14T08:46:59.979Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `22`
- Chain head: `64b6a02e5f64a7a000a9ea9acede9ab401d759d3216257ad1bea797d49f57a81`
