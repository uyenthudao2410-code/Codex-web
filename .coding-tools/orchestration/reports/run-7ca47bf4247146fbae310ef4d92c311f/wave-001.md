# Orchestration Wave 1

- Run: `7ca47bf4247146fbae310ef4d92c311f`
- Wave: `4a5d5e767d8243d38afccde2d03df300`
- Objective: Implement the smallest fail-closed acceptance fix: allow cached clients to transport acceptance_files only as payload.acceptance_files for action=accept, reject ambiguous/extra payload fields, and allow explicitly SHA-attested pre-existing dirty files only when they are inside the write lease and durable patch_surface_observed. Preserve ordinary acceptance exclusion of pre-existing dirty files and all protected/reparse/path guards. Update focused tests only.
- Objective revision: `1`
- Objective SHA-256: `d1f6f0e92e9eae508b53b530a42421dffb732790526b84d7056dfd531b54741f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9`
- Worktree fingerprint: `c018c4b51dce7536ed808871c65aa9d70ec7c7cf3949a6f4662c707aa1aec7be`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 29985 | 2026-08-26T04:32:35.478Z | run_started |  | PREFLIGHT |  |
| 29986 | 2026-08-26T04:32:46.469Z | observation_span_recorded |  |  |  |
| 29987 | 2026-08-26T04:34:39.815Z | solution_shadow_recommended |  |  |  |
| 29988 | 2026-08-26T04:34:43.167Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 29989 | 2026-08-26T04:34:43.279Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 29990 | 2026-08-26T04:34:44.923Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 29991 | 2026-08-26T04:36:39.810Z | managed_process_admitted |  |  | owner=default |
| 29992 | 2026-08-26T04:36:40.043Z | managed_process_started |  |  | owner=default |
| 29993 | 2026-08-26T04:36:40.378Z | managed_process_terminal |  |  | owner=default |

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
- Events checked: `9`
- Chain head: `a7e0c405c8ded0ac9497823da3d30d5859d09c2ea43d9d7c407341114d632bb6`
