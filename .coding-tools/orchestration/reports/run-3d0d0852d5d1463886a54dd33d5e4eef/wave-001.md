# Orchestration Wave 1

- Run: `3d0d0852d5d1463886a54dd33d5e4eef`
- Wave: `e6b35e273828461cbd476ce26d645f9a`
- Objective: Natural Codex-web bugfix: make lifecycle census projection source selection fail closed against stale unscoped global task-state. When valid contextual task projections exist, they must be evaluated instead of being masked by any non-empty global projection; preserve global fallback only when contextual projections are absent, preserve existing lifecycle classifications/read-only invariants, and add a focused regression for stale global ACCEPTING versus contextual CHECKPOINTED.
- Objective revision: `1`
- Objective SHA-256: `13333dbf40b6aff9f56301d5874b6ed072dbe0608b3f245119bb5eb4078fd1c6`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `ff69f258efc46ecc7713cebf1b5b77a10326f2ac4355c22111a141ce325d2a8c`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 45139 | 2026-09-09T06:57:25.471Z | run_started |  | PREFLIGHT |  |
| 45140 | 2026-09-09T06:57:25.942Z | observation_span_recorded |  |  |  |
| 45141 | 2026-09-09T06:57:26.139Z | solution_shadow_recommended |  |  |  |
| 45142 | 2026-09-09T06:57:36.079Z | observation_span_recorded |  |  |  |
| 45143 | 2026-09-09T06:57:36.280Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 45144 | 2026-09-09T06:59:04.701Z | managed_process_admitted |  |  | owner=default |
| 45145 | 2026-09-09T06:59:05.035Z | managed_process_started |  |  | owner=default |
| 45146 | 2026-09-09T06:59:06.325Z | managed_process_terminal |  |  | owner=default |
| 45147 | 2026-09-09T06:59:16.589Z | managed_process_admitted |  |  | owner=default |
| 45148 | 2026-09-09T06:59:16.989Z | managed_process_started |  |  | owner=default |
| 45149 | 2026-09-09T06:59:35.402Z | managed_process_terminal |  |  | owner=default |
| 45150 | 2026-09-09T07:01:26.010Z | managed_process_admitted |  |  | owner=default |
| 45151 | 2026-09-09T07:01:26.327Z | managed_process_started |  |  | owner=default |
| 45152 | 2026-09-09T07:01:26.738Z | managed_process_terminal |  |  | owner=default |
| 45153 | 2026-09-09T07:05:24.380Z | state_transition | PREFLIGHT | ABORTED | reason=Prepared caller-scoped binding was invalidated by the mandatory pre-mutation command task projection. Audit proves no write lease, delegation, mutation receipt, or proof was created; exact source diff remained empty. Terminalize this failed preflight attempt before creating a new engineering attempt under the same natural Problem Revision. |
| 45154 | 2026-09-09T07:05:24.840Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `16`
- Chain head: `0ae2120b76cb3b01ff474f4fb58d209ce68283fdf454876c9b0430d9130f4c8e`
