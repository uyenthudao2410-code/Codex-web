# Orchestration Wave 2

- Run: `6d2f15fe1c6d46708ed75551fa13ffb4`
- Wave: `573d50c53df8453381332614a4f13912`
- Objective: Complete the lifecycle/economics correctness fix from the single paid Flash canary evidence without any further provider inference. Correlated finish=tool-calls must remain an active dispatch step; aggregate per-message measured economics idempotently; emit canonical UsageEvent only at true delegation terminal or Adapter terminal failure; freeze conflicting post-terminal metadata; add bounded Adapter lifecycle evidence and a specific idle-timeout-after-tool-calls error. Preserve canary utility/package and all public contracts.
- Mode: `mcp_only`
- Base HEAD: `bf072d9bd08a14768b729c1d209367bc771633a5`
- Worktree fingerprint: `14ccb4ce72657f538f83348b8c2a5cf2620aefaef4b0b76d366af5d349acbb09`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2099 | 2026-08-14T13:01:52.178Z | wave_replanned |  | PREFLIGHT | reason=The prior split patch partially succeeded: exact inspection shows only orchestration_ledger.py and usage_events.py were applied before an ambiguous server hunk stopped execution. This replan preserves those verified partial changes and narrows mutation to remaining files, using whole-function/unique test anchors; it also persists bounded Adapter lifecycle_evidence into delegation metadata for postmortem usefulness. |
| 2100 | 2026-08-14T13:01:52.339Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2101 | 2026-08-14T13:01:52.429Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2102 | 2026-08-14T13:01:52.521Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2103 | 2026-08-14T13:01:52.645Z | state_transition | READY | ROUTED | reason=route_selected |
| 2104 | 2026-08-14T13:01:52.996Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=006378fcb6bb4cbe8cc793fb23c14c88 |
| 2105 | 2026-08-14T13:01:53.096Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2106 | 2026-08-14T13:01:53.695Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=006378fcb6bb4cbe8cc793fb23c14c88 |
| 2107 | 2026-08-14T13:01:53.778Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 2108 | 2026-08-14T13:01:54.093Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 2109 | 2026-08-14T13:01:54.195Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |

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
- Events checked: `33`
- Chain head: `3f651b4fbfde58330df4adf5344b6574fea63b30b11341658ebd210d27d11c01`
