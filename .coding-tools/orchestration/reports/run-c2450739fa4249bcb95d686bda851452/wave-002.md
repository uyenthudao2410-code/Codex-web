# Orchestration Wave 2

- Run: `c2450739fa4249bcb95d686bda851452`
- Wave: `b466ecbeef204d42a1fbdbb85ff91e63`
- Objective: Natural #22 causal repair: prevent generic mutating-tool auto-start from archiving/replacing a failed task when that task still projects an exact nonterminal EOCL run. Preserve direct TaskStateStore.ensure_started semantics used by recovery fixtures and preserve normal replacement for terminal/no-run tasks. Add a focused stateless regression for failed presentation task plus canonical PREFLIGHT run.
- Objective revision: `2`
- Objective SHA-256: `32420ca5f62870da647fc8f61d49ce8cf51a13030bcae3eca77839498ec67821`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `b5450a7ede1afdefe715132cb5f827450428f80db8331ad37691797177fecc56`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47528 | 2026-09-10T10:38:26.334Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 entered REPLAN before first write because its worktree fingerprint changed during evidence collection. No source mutation occurred. New evidence localizes the cause to generic server tool auto-start replacing a failed presentation task while its EOCL run remains nonterminal; scope is now narrowed to task-state tool-start guard, one server dispatch call-site, and a focused stateless regression. |
| 47529 | 2026-09-10T10:38:26.633Z | observation_span_recorded |  |  |  |
| 47530 | 2026-09-10T10:38:32.640Z | observation_span_recorded |  |  |  |
| 47531 | 2026-09-10T10:38:32.946Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47532 | 2026-09-10T10:40:15.384Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 47533 | 2026-09-10T10:40:15.569Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 47534 | 2026-09-10T10:40:15.739Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `160`
- Chain head: `407dd1e3990cec4fbc266b2d4a2e336343b34d45a602b1437588121b9a6b79b8`
