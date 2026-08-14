# Orchestration Wave 2

- Run: `200332da9f66499f8ff36e42c0d93005`
- Wave: `274468e1b1be4bd38b74e9b5dfcbecf6`
- Objective: Fix the Execution Control Center analytics projection and evidence semantics without changing layout, routing policy, or the public MCP contract. The dashboard must consume PerformanceTraceStore.recent (legacy records fallback only), derive context-token equivalents only from measured model_visible_bytes, never from request/response transport bytes, and prefer measured numeric delegation economics for model rows. Clearly mark MEASURED vs ESTIMATED and SCENARIO cost. Preserve all concurrent UI work.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `2467f86778778423c80bfecf7018a939e6c0d28cf92f2aa16721614f594428bb`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1645 | 2026-08-14T08:47:33.978Z | wave_replanned |  | PREFLIGHT | reason=The previous Wave 2b patch was rejected before mutation because repeated loop fragments matched multiple functions. Exact function bodies are now localized; replace whole functions to make anchors unambiguous. |
| 1646 | 2026-08-14T08:47:34.153Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1647 | 2026-08-14T08:47:34.388Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1648 | 2026-08-14T08:47:34.572Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1649 | 2026-08-14T08:47:34.748Z | state_transition | READY | ROUTED | reason=route_selected |
| 1650 | 2026-08-14T08:47:35.421Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=12ade408a56d44f0beb2101ea2c731c0 |
| 1651 | 2026-08-14T08:47:35.605Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1652 | 2026-08-14T08:47:36.365Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=12ade408a56d44f0beb2101ea2c731c0 |
| 1653 | 2026-08-14T08:47:36.561Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1654 | 2026-08-14T08:47:37.345Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1655 | 2026-08-14T08:47:52.682Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 982b96c950764cb997134f9f905ce0c4 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 |  | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `22`
- Chain head: `64b6a02e5f64a7a000a9ea9acede9ab401d759d3216257ad1bea797d49f57a81`
