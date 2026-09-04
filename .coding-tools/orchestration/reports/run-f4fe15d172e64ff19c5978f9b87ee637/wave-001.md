# Orchestration Wave 1

- Run: `f4fe15d172e64ff19c5978f9b87ee637`
- Wave: `3308e66d376a4accaeac114ab3f72667`
- Objective: Redesign the Codex-web Control Center/dashboard for a basic end user: prioritize token quantification and accepted-result optimization metrics; remove most technical/runtime/orchestration details from the default dashboard surface while preserving all technical telemetry in underlying state and code for diagnostics. The primary view should emphasize controller usage (exact when available, calibrated estimate when not), provider exact tokens, combined/normalized compute, trend/comparison, accepted-result efficiency, and clear measurement confidence. Technical fields such as trace/RUN/WAVE/activation/process/server/schema/provenance should not occupy the default user-facing dashboard, though they remain available internally or in an advanced diagnostics section. Do not change accounting truth semantics: estimated values must never be labeled exact, unknown must never become zero, and API-equivalent cost must not be presented as ChatGPT billing. Prepare only; inspect current UI/data flow/tests and return the smallest coherent implementation scope and proof plan.
- Objective revision: `1`
- Objective SHA-256: `a2b4ddd80622e11e795941417a7debd3f25283874cd04bca105542fe28a10a6f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `ce5e0119b3d0b8796fb1c6988df9d6e82539ab4a496753e7a8694e3445d31376`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39038 | 2026-09-03T23:55:02.701Z | run_started |  | PREFLIGHT |  |
| 39039 | 2026-09-03T23:55:03.366Z | observation_span_recorded |  |  |  |
| 39040 | 2026-09-03T23:55:09.203Z | observation_span_recorded |  |  |  |
| 39041 | 2026-09-03T23:55:09.428Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 39043 | 2026-09-03T23:56:24.297Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39045 | 2026-09-03T23:56:24.906Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39049 | 2026-09-03T23:56:26.022Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39067 | 2026-09-03T23:56:36.813Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39068 | 2026-09-03T23:56:37.203Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39069 | 2026-09-03T23:56:37.776Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39080 | 2026-09-03T23:57:10.388Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39081 | 2026-09-03T23:57:10.772Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39082 | 2026-09-03T23:57:11.689Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39083 | 2026-09-03T23:57:18.479Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39084 | 2026-09-03T23:57:18.872Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39085 | 2026-09-03T23:57:20.078Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39086 | 2026-09-03T23:57:33.144Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39087 | 2026-09-03T23:57:33.571Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39088 | 2026-09-03T23:57:34.491Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39089 | 2026-09-03T23:57:41.445Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39090 | 2026-09-03T23:57:41.854Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39091 | 2026-09-03T23:57:42.673Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39092 | 2026-09-03T23:58:29.779Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39093 | 2026-09-03T23:58:30.229Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39094 | 2026-09-03T23:58:30.988Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39112 | 2026-09-03T23:59:19.987Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39113 | 2026-09-03T23:59:20.404Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39114 | 2026-09-03T23:59:21.119Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39119 | 2026-09-03T23:59:33.658Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard |
| 39120 | 2026-09-03T23:59:34.064Z | managed_process_started |  |  | owner=chatweb-token-dashboard |
| 39121 | 2026-09-03T23:59:35.029Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard |
| 39158 | 2026-09-04T00:29:13.692Z | state_transition | PREFLIGHT | ABORTED | reason=Superseded by the exact accepted four-file dashboard result in RUN 6c59a857595a410d80eed85a343d58da / WAVE ffe24d8791a14e9b9b600f33f46abe62 / checkpoint 1ac6fb37284140229807f6ddf18acc44. Fail closed rather than duplicate adoption, proof, or acceptance. |
| 39159 | 2026-09-04T00:29:14.224Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `33`
- Chain head: `af504acd747feea1d13a4b6970879f952ba798df35622e5472dd42c3b6e6b45e`
