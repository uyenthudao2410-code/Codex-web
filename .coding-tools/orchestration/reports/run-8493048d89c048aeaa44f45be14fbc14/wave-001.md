# Orchestration Wave 1

- Run: `8493048d89c048aeaa44f45be14fbc14`
- Wave: `ba85235190894dde9cc39eadd39a49cf`
- Objective: Prepare the narrow R2B automatic server-preferred dispatch slice on top of accepted server_compute opt-in. Inspect current Cargo read-only validation flow and compute placement adapter to implement source-authoritative HEAVY offload only for cargo_check/cargo_test when timeout has durable-job handoff headroom and sandbox is absent. Source Runner must supply full clean exact HEAD; candidate compute Runner must be a different Runner, explicitly server_compute=true, same logical project id, exact same full clean HEAD, structured validation + exact-source capable, fresh and within known job capacity. If no eligible target, preserve current source Runner behavior. No cross-runner retry, no dirty snapshot, no mutating cargo_fmt offload, no public tool schema changes. Determine exact current methods for listing auth-visible clients/jobs and canonical runtime project resolution, and exact test helpers for multi-runner validation dispatch.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `6d0447e985e54ba1648005e0627bec3ca0270d3f58a9f3f58eaac13289e6507a`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8059 | 2026-08-16T12:43:10.591Z | run_started |  | PREFLIGHT |  |
| 8060 | 2026-08-16T12:43:13.480Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8061 | 2026-08-16T12:44:29.030Z | managed_process_admitted |  |  | owner=default |
| 8062 | 2026-08-16T12:44:29.280Z | managed_process_started |  |  | owner=default |
| 8063 | 2026-08-16T12:44:29.698Z | managed_process_terminal |  |  | owner=default |
| 8064 | 2026-08-16T12:58:23.819Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 8065 | 2026-08-16T12:58:23.941Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 8066 | 2026-08-16T12:58:24.075Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `172`
- Chain head: `e7827db97a33ae955a83687a56516ee6906376b1ec5710730e6ea409f48dc24d`
