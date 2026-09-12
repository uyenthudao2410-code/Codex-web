# Orchestration Wave 1

- Run: `babe1bae0d534f0f8421374227adcd5a`
- Wave: `49b4e416a83246388ec37965b0c0a0d0`
- Objective: Fix PRL prl-a5bf3e0510b110459e4cf57f5bcde24b: in RecoveryHost.superviseOnce, when the direct serviceSupervisorRestartRequest attempt returns status=deferred with a retained durable restart journal (notably transient RUNTIME_BUSY while the initiating task_control call is still leaving admission), do not fall through into orchestrator.supervise in the same watchdog tick because orchestrator.supervise calls serviceSupervisorRestartRequest again. Return a fail-closed transitional supervision projection for that tick; allow the next watchdog tick to retry. Add a focused regression test that reproduces deferred-first then accepted-on-next-tick ordering and proves no same-tick second consumption, no ordinary supervise/recovery/UI work on the deferred tick, and the accepted tick yields immediately for handoff. Preserve all activation fences, durable journal semantics, exact identity checks, and unrelated dirty worktree changes.
- Objective revision: `1`
- Objective SHA-256: `76cd9c22f3fc231d4ec54c83845b294f7864d67a1e989d880e0057dbd90d2950`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `6eb7d200b22c3598ba6a0b798705b597c5433b2eeeb36f59fb87f20177b620dc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 49667 | 2026-09-11T09:22:01.042Z | run_started |  | PREFLIGHT |  |
| 49668 | 2026-09-11T09:22:01.581Z | observation_span_recorded |  |  |  |
| 49669 | 2026-09-11T09:22:01.779Z | solution_shadow_recommended |  |  |  |
| 49670 | 2026-09-11T09:22:07.669Z | observation_span_recorded |  |  |  |
| 49671 | 2026-09-11T09:22:07.870Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 49672 | 2026-09-11T09:23:16.820Z | managed_process_admitted |  |  | owner=default |
| 49673 | 2026-09-11T09:23:17.160Z | managed_process_started |  |  | owner=default |
| 49674 | 2026-09-11T09:23:17.712Z | managed_process_terminal |  |  | owner=default |
| 49675 | 2026-09-11T09:23:55.212Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 49676 | 2026-09-11T09:23:55.401Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 49677 | 2026-09-11T09:23:55.601Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 49678 | 2026-09-11T09:23:55.812Z | state_transition | READY | ROUTED | reason=route_selected |
| 49679 | 2026-09-11T09:23:56.049Z | observation_span_recorded |  |  |  |
| 49680 | 2026-09-11T09:25:22.028Z | failure_observed | ROUTED | ROUTED | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 49681 | 2026-09-11T09:25:22.209Z | state_transition | ROUTED | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 49682 | 2026-09-11T09:25:22.437Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `326`
- Chain head: `0ec6738f6d548fe6b72ddcbf21169e5517df57d43a6a365e26b7e46224cd43c8`
