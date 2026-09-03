# Orchestration Wave 4

- Run: `9f686c0058f743c0a15d866922983ac2`
- Wave: `fb29eb0fdb8f4fdf9df0a3dd00ba3a48`
- Objective: W8 only: implement the budget/reservation control defined by docs/research/260901_CODING_WEB_TOKEN_USAGE_COST_CONTEXT_OBSERVABILITY_AND_ACCEPTED_RESULT_EFFICIENCY_MASTER_PLAN.md on top of accepted W1-W7. Preserve unknown_not_zero, never convert bytes to tokens, never treat estimates as observed spend, preserve exact 8-tool smart-v3 public MCP contract, fail closed on missing/stale reservation authority, and keep controller/provider/tool-card accounting planes distinct. Exclude W9 history analytics and W10 representative E2E closure. Do not commit, push, restart, package, release, or deploy. First localize the exact W8 contract, existing budget/credit/routing admission surfaces, reservation lifecycle authority, smallest causal change set, and focused deterministic proof plan while preserving unrelated dirty work.
- Objective revision: `1`
- Objective SHA-256: `505f6c1333dad0dafe302b0b2d2828cb326fc58c48009987c5dcbec79349760d`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `bfd17766ca0b2c128875d7811865e09b205f58c02865be4baf5303e0734316af`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35056 | 2026-09-01T23:46:15.652Z | wave_replanned |  | PREFLIGHT | reason=Changed W8 strategy after verification-only wave a80b10296481485abd5623bcbea77478 was rejected and report fb015efb73a2b3af9f6a8cccc94168077b8b5666a5b25b7e82a305e7a77e9a08 acknowledged. Open a replacement wave in the same RUN for exact source localization before an explicit guarded patch. Do not run acceptance proof yet and do not mutate during prepare. Existing task-level solution shadow remains authoritative. Localize provider admission, terminal synchronization, exact telemetry correlation, traffic reservation state, and focused tests needed for durable UsageReservation -> actual UsageEvent reconciliation. |
| 35057 | 2026-09-01T23:46:15.924Z | observation_span_recorded |  |  |  |
| 35058 | 2026-09-01T23:46:17.101Z | observation_span_recorded |  |  |  |
| 35059 | 2026-09-01T23:46:17.371Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35060 | 2026-09-01T23:46:35.584Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35061 | 2026-09-01T23:47:25.639Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35062 | 2026-09-01T23:47:51.383Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35063 | 2026-09-01T23:49:02.573Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35064 | 2026-09-01T23:49:18.242Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35081 | 2026-09-02T00:02:35.825Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35082 | 2026-09-02T00:03:14.506Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35083 | 2026-09-02T00:04:15.669Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35084 | 2026-09-02T00:04:30.041Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35085 | 2026-09-02T00:05:26.877Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35086 | 2026-09-02T00:05:43.413Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35087 | 2026-09-02T00:07:29.965Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35088 | 2026-09-02T00:08:11.549Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 35089 | 2026-09-02T00:11:49.921Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35090 | 2026-09-02T00:11:50.169Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35091 | 2026-09-02T00:11:50.401Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 35092 | 2026-09-02T00:11:50.622Z | state_transition | READY | ROUTED | reason=route_selected |
| 35093 | 2026-09-02T00:11:50.843Z | observation_span_recorded |  |  |  |
| 35094 | 2026-09-02T00:11:52.043Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=215b0304c64145719d9df5951a657014 |
| 35095 | 2026-09-02T00:11:52.271Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35096 | 2026-09-02T00:11:53.224Z | patch_surface_observed |  |  |  |
| 35097 | 2026-09-02T00:11:53.466Z | patch_surface_observed |  |  |  |
| 35098 | 2026-09-02T00:11:53.712Z | patch_surface_observed |  |  |  |
| 35099 | 2026-09-02T00:11:53.951Z | patch_surface_observed |  |  |  |
| 35100 | 2026-09-02T00:11:54.211Z | patch_surface_observed |  |  |  |
| 35101 | 2026-09-02T00:11:54.536Z | patch_surface_observed |  |  |  |
| 35102 | 2026-09-02T00:11:54.756Z | observation_span_recorded |  |  |  |
| 35103 | 2026-09-02T00:11:55.073Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=215b0304c64145719d9df5951a657014 |
| 35104 | 2026-09-02T00:11:55.217Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35105 | 2026-09-02T00:11:56.013Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=32df8d8a6040ee08e8a929749157b6b3e9402539530d28fb4c43b6ce1bb0bb90 |
| 35106 | 2026-09-02T00:11:56.249Z | observation_span_recorded |  |  |  |
| 35107 | 2026-09-02T00:11:56.477Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 35108 | 2026-09-02T00:11:56.647Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 35109 | 2026-09-02T00:11:56.816Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `213`
- Chain head: `c1a389deacb2a94e0d3a41945bc45e06a8683ae9fd08dc14ea77507c7bac983a`
