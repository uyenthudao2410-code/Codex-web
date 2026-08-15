# Orchestration Wave 1

- Run: `d455e965665f474f9827a0c511df6049`
- Wave: `90875af5740f401b8358b8bfb72c3188`
- Objective: Reduce dominant replan/rework causes without changing routing or acceptance policy. Add deterministic caller-patch batch preflight before EOCL run creation so disjoint ambiguous/context-invalid patches fail before any run/write/partial mutation; add bounded candidate line diagnostics for ambiguous hunks; and make agent_workflow/verify_build honor the existing workdir argument for test/build commands. Add focused regressions only. Preserve Smart-v3 tool count, provider gates, EOCL authority, cost-attribution work, and unrelated dirty files. Do not call providers or external review.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `b44ac9c6ef6df9dcbc2aaa5baa6815f7cffe444602be42c9bcb3d6cdaa253153`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4420 | 2026-08-15T05:25:23.230Z | run_started |  | PREFLIGHT |  |
| 4421 | 2026-08-15T05:25:23.401Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4422 | 2026-08-15T05:25:23.584Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4423 | 2026-08-15T05:25:23.755Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4424 | 2026-08-15T05:25:24.005Z | state_transition | READY | ROUTED | reason=route_selected |
| 4425 | 2026-08-15T05:25:24.620Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=80dc6ab5fb5741568f0d443933dc2086 |
| 4426 | 2026-08-15T05:25:24.800Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4427 | 2026-08-15T05:25:25.375Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 4428 | 2026-08-15T05:25:25.684Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=80dc6ab5fb5741568f0d443933dc2086 |
| 4429 | 2026-08-15T05:25:25.883Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `23`
- Chain head: `55361231148c6956011b763cf8d41b4f40c3f1b7ce1bda23e41d634608284996`
