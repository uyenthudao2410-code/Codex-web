# Orchestration Wave 1

- Run: `2d02657290524fc0b8da686e4b0ed7b9`
- Wave: `231d6e0028134903a87b6a31498e5285`
- Objective: Validate and accept the exact completed source for permanent direct Windows host execution without ProcessContainer or Windows Sandbox, preserving permission controls, existing workspace/node identity and unrelated work.
- Objective revision: `1`
- Objective SHA-256: `6600e4dfcbc503504f05e4750077f016ba4dc14a54cb86e1950e65da3387a626`
- Objective source: `run_initial_objective`
- Mode: `auto`
- Base HEAD: `5c5e207265f56a69b72f16dd78c4d2951f382609`
- Worktree fingerprint: `1b6d9f21700afc713dcc59c929216669b833eba7da32637ae17a2a4650852c49`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 61515 | 2026-10-22T07:15:07.393Z | run_started |  | PREFLIGHT |  |
| 61516 | 2026-10-22T07:15:07.735Z | observation_span_recorded |  |  |  |
| 61517 | 2026-10-22T07:15:08.677Z | observation_span_recorded |  |  |  |
| 61518 | 2026-10-22T07:15:08.891Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 61519 | 2026-10-22T07:15:30.404Z | controller_transferred | PREFLIGHT | PREFLIGHT |  |
| 61520 | 2026-10-22T07:15:31.580Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 61521 | 2026-10-22T07:15:31.776Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 61522 | 2026-10-22T07:15:31.957Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 61523 | 2026-10-22T07:17:09.874Z | controller_transferred | REPLAN | REPLAN |  |
| 61524 | 2026-10-22T07:17:40.336Z | controller_transferred | REPLAN | REPLAN |  |

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
- Events checked: `40`
- Chain head: `4954f4b413b2cae8e0d13e9f6b688d1dd453d84aa837a78c78fae98f6c70cd7b`
