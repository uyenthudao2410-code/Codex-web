# Orchestration Wave 1

- Run: `482171d427dc4fdfb3c9b3e28cc42552`
- Wave: `e870fc6ffc164e26a08e49a9b38d94c3`
- Objective: Implement token-accounting wave 2 only: canonical non-overlapping pricing; durable exact 7-day UsageEvent analytics across all runs with hourly UTC/by actor/provider/model/rolling 5m; strict conflicting usage_id rejection; provider economics excludes controller actor; expose analytics in control orchestration snapshot. Preserve accepted UsageEvent v2 and all unrelated work. No ChatWeb ingress/dashboard yet. No commit/push/restart.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `af51dd99ac8dcb2d7867a94c63e109eca4cd6fcf72168580485ad7d02c25751e`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21052 | 2026-08-19T08:58:49.387Z | run_started |  | PREFLIGHT |  |
| 21053 | 2026-08-19T08:58:50.361Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21054 | 2026-08-19T08:59:02.980Z | solution_shadow_recommended |  |  |  |
| 21055 | 2026-08-19T08:59:21.688Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21056 | 2026-08-19T08:59:37.260Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21057 | 2026-08-19T09:00:34.247Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21058 | 2026-08-19T09:00:39.547Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21059 | 2026-08-19T09:00:39.693Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21060 | 2026-08-19T09:00:39.912Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21061 | 2026-08-19T09:00:40.054Z | state_transition | READY | ROUTED | reason=route_selected |
| 21062 | 2026-08-19T09:00:40.587Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e16d80a77e864369bd8caa22666c60fb |
| 21063 | 2026-08-19T09:00:40.834Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21064 | 2026-08-19T09:00:41.259Z | patch_surface_observed |  |  |  |
| 21065 | 2026-08-19T09:00:41.409Z | patch_surface_observed |  |  |  |
| 21066 | 2026-08-19T09:00:41.545Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 21067 | 2026-08-19T09:00:41.787Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=e16d80a77e864369bd8caa22666c60fb |
| 21068 | 2026-08-19T09:00:41.971Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |
| 21069 | 2026-08-19T09:00:42.195Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `65`
- Chain head: `e9c5b9abd9c739f7042d273b2ccfe1baf4cf104b2042c4886645fecf71d6e28b`
