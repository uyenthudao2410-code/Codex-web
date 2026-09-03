# Orchestration Wave 1

- Run: `3e373f0a22414388be48d9fdf61a2f28`
- Wave: `59b907974c1f45ff8dc8d8ea0c5ff84f`
- Objective: Close H0/H1 for ChatWeb controller token measurement with content-free attested envelope evidence. Reuse the existing connector/runtime observation plane; do not add a public tool or infer tokens. Record only whether the exact io.coding-tools/controllerUsage key was present on attested ChatWeb tools/call envelopes, aggregate current-process present/absent counts, expose this in authenticated health and live ChatWeb measurement projection, and explicitly report that no supported post-turn controller-usage sideband exists yet. Preserve existing exact controller UsageEvent ingress and all unrelated dirty hunks. Add focused regressions proving absent envelopes remain unknown/not-zero, present envelopes are observed alongside existing exact usage ingestion, and live projection stays fail-closed.
- Objective revision: `1`
- Objective SHA-256: `2c7bbba402f23976c453a6a2254b457d743dbd162bc428dd322fae3085e98352`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `67e483cebe04c03788e5376d5c309751029a51ed47a15a9a74cc2a2a16fa2ee1`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36198 | 2026-09-03T04:57:56.644Z | run_started |  | PREFLIGHT |  |
| 36199 | 2026-09-03T04:57:56.975Z | observation_span_recorded |  |  |  |
| 36200 | 2026-09-03T04:57:57.197Z | solution_shadow_recommended |  |  |  |
| 36201 | 2026-09-03T04:57:57.390Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36202 | 2026-09-03T04:57:57.626Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36203 | 2026-09-03T04:57:57.863Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36204 | 2026-09-03T04:57:58.045Z | state_transition | READY | ROUTED | reason=route_selected |
| 36205 | 2026-09-03T04:57:58.272Z | observation_span_recorded |  |  |  |
| 36206 | 2026-09-03T04:58:47.649Z | failure_observed | ROUTED | ROUTED | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 36207 | 2026-09-03T04:58:47.878Z | state_transition | ROUTED | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 36208 | 2026-09-03T04:58:48.136Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `41`
- Chain head: `2753f63a47fcafff15213b8a3aa8b83fb318aa46355e7674dbb37363652ac235`
