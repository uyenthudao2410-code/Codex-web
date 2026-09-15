# Orchestration Wave 1

- Run: `507227665bb742e0b95078c0072f21df`
- Wave: `275a64e19e73425895eedcc6d091909c`
- Objective: Read-only trace of the exact agent_workflow continuation-grant call path that invokes build_goal_continuation_policy/build_run_continuation_policy. Determine which contract_fingerprint value is passed into continuation policy construction and why a canonical 64-hex Problem contract fingerprint can still produce RUN_CONTINUATION_POLICY_INVALID. Do not mutate source, create a continuation grant, restart runtime, or alter acceptance authority.
- Objective revision: `1`
- Objective SHA-256: `c4f351393b2037b76f535428eeada2d315f31536b5f91d22e720d7ebeb435a5e`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `6a03b8b995bb3b11ddb3a463e6b7e28621ff59579eab3bb288ce69038f89aa10`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58349 | 2026-09-15T08:11:09.835Z | run_started |  | PREFLIGHT |  |
| 58350 | 2026-09-15T08:11:14.090Z | observation_span_recorded |  |  |  |
| 58351 | 2026-09-15T08:11:21.440Z | observation_span_recorded |  |  |  |
| 58352 | 2026-09-15T08:11:22.086Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58369 | 2026-09-15T08:11:45.749Z | managed_process_admitted |  |  | owner=chatweb |
| 58370 | 2026-09-15T08:11:46.438Z | managed_process_started |  |  | owner=chatweb |
| 58371 | 2026-09-15T08:11:47.151Z | managed_process_terminal |  |  | owner=chatweb |
| 58503 | 2026-09-15T08:29:08.265Z | controller_knowledge_read_observed |  |  |  |
| 58507 | 2026-09-15T08:30:28.244Z | state_transition | PREFLIGHT | ABORTED | reason=Terminalize this same-flow read-only diagnostic RUN before the explicitly authorized controlled restart. It is PREFLIGHT-only, has no write lease, no modified files, no managed jobs/effects, and its diagnostic objective is superseded. Preserve audit; do not touch C01 ACCEPTING. |
| 58508 | 2026-09-15T08:30:29.339Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `10`
- Chain head: `96460359ed77f6ab7ae1fcacd143a3d9593205524e8302f65dbe462c02fce628`
