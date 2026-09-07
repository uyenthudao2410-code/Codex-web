# Orchestration Wave 1

- Run: `af844dcf2f444c15ad35a27002b38372`
- Wave: `5f275779d9064bd488b2b6326ccd6055`
- Objective: Pin the exact fresh-install activation trigger/wiring defect on current main without repeating broad investigation. Inspect only electron/main.js and electron/services/recoveryHost.js. Find where FullCleanActivationManager is constructed or invoked, every branch that calls activate()/resume/recovery activation, and the first-ever installed startup branch when there is no durable activation epoch/ready receipt. Reconstruct the exact condition that can leave MCP running with activation gate CLOSED while connector_compatibility_bootstrap is accepted, snapshot_busy=false, ready_commit_digest=null and workspace calls loop on RUNTIME_ACTIVATION_PENDING. Return exact symbols/conditions and smallest causal patch boundary. Do not mutate.
- Objective revision: `1`
- Objective SHA-256: `11732a21d3af76d92468445f04a6fd7e1bf4565f0d3fda7f1a6fb99aed4fe963`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41563 | 2026-09-06T05:51:24.042Z | run_started |  | PREFLIGHT |  |
| 41564 | 2026-09-06T05:51:24.358Z | observation_span_recorded |  |  |  |
| 41565 | 2026-09-06T05:51:29.521Z | observation_span_recorded |  |  |  |
| 41566 | 2026-09-06T05:51:29.670Z | context_prepared | PREFLIGHT | PREFLIGHT |  |

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
- Events checked: `4`
- Chain head: `79cd6089045353038f91112705c60c33e3ef545585af5f48912b3944abe44bbe`
