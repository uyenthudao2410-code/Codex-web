# Orchestration Wave 1

- Run: `b47a98a98be442af9bac7b4ac79091bf`
- Wave: `6a3100ecb87e4bccbfd4ba19fd1aee02`
- Objective: Pin the exact fresh-install trigger/wiring bug. On current main, inspect only the startup/recovery code that constructs FullCleanActivationManager and decides whether to call activate(), resume activation, or merely leave MCP running with activation CLOSED. Reconstruct the first-ever installed start when there is no durable activation epoch/ready receipt. Find the exact branch that can yield: connector_compatibility_bootstrap accepted=true, snapshot_busy=false, ready_commit_digest=null, configured_gate=CLOSED, admission CLOSED, and repeated RUNTIME_ACTIVATION_PENDING. Distinguish initial install, ordinary reattach, recovery after stale owner, and already-completed activation. Return exact symbols/conditions and the smallest causal patch boundary; do not mutate.
- Objective revision: `1`
- Objective SHA-256: `4e5bb20c65edfe83725b3386cf23d3c025617baa447886eca6f7816bda352d37`
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
| 41539 | 2026-09-06T05:50:38.721Z | run_started |  | PREFLIGHT |  |
| 41540 | 2026-09-06T05:50:39.107Z | observation_span_recorded |  |  |  |
| 41541 | 2026-09-06T05:50:43.787Z | observation_span_recorded |  |  |  |
| 41542 | 2026-09-06T05:50:43.975Z | context_prepared | PREFLIGHT | PREFLIGHT |  |

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
- Chain head: `5359f1a01b205117a3fbdce32580eedf3657ab925c18ab2f62c712c2e951665f`
