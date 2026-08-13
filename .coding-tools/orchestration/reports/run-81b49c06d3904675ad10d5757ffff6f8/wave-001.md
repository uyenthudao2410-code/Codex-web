# Orchestration Wave 1

- Run: `81b49c06d3904675ad10d5757ffff6f8`
- Wave: `038c1990a6f4484d869fc95947ad786e`
- Objective: Fix the confirmed WEBCODEX_MCP_MODEL_SURFACE cross-test race in src/mcp_tests.rs only. Ordinary test_runtime() must be deterministic LocalCoding and never read process env. Normal full-operator MCP tests must inject ModelSurface::FullOperatorRuntime explicitly (helper is fine). Add a separate test_runtime_from_env() that resolves process env and use it only in tests explicitly validating env-driven model-surface selection/immutability; those tests must hold admin_cli::TEST_ENV_LOCK and restore/remove the env variable. Remove full_operator_mcp_env/full_operator_mcp_env_locked from ordinary tests and delete them if no longer needed. Preserve TEST_ENV_LOCK around WEBCODEX_MCP_COMPACT_SCHEMAS mutations. Do not change production code, OAuth/MCP authorization, or model-facing tool sets. Verify cargo fmt --check and focused Rust tests for oauth2_mcp_tools_list_requires_runtime_read, explicit_local_coding_v1_selects_local_coding, explicit_full_operator_v1_reports_full_operator_surface, and selected_surface_is_immutable_after_environment_changes. Finally verify every MCP_MODEL_SURFACE_ENV mutation in src/mcp_tests.rs is lock-protected and no ordinary runtime construction depends on model-surface env.
- Mode: `deep_single_lane`
- Base HEAD: `db7725e3601afc2692627a0b4eef674d599bd17e`
- Worktree fingerprint: `88b765e4cf53d9a3853a7c1868ea0a694e44eda49547a0e83922dea6f8fffae3`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| 564a5be231904bee99a65f84de5ccc9b | CODEX:sol_xhigh | auto | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 424 | 2026-08-13T17:37:24.360Z | run_started |  | PREFLIGHT |  |
| 425 | 2026-08-13T17:37:24.679Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 426 | 2026-08-13T17:37:24.757Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 427 | 2026-08-13T17:37:24.915Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=deep_single_lane |
| 428 | 2026-08-13T17:37:24.995Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 429 | 2026-08-13T17:37:25.079Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 430 | 2026-08-13T17:37:25.190Z | route_selected | READY | READY | reason=deep_or_broad_context; requested=auto; resolved=sol_xhigh |
| 431 | 2026-08-13T17:37:25.297Z | state_transition | READY | ROUTED | reason=route_selected |
| 432 | 2026-08-13T17:37:25.473Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 433 | 2026-08-13T17:37:25.568Z | model_dispatch_started | ROUTED | ROUTED |  |
| 434 | 2026-08-13T17:37:59.745Z | model_dispatch_finished | ROUTED | ROUTED | status=interrupted |
| 435 | 2026-08-13T17:37:59.924Z | delegation_finished | ROUTED | ROUTED | reason=candidate_model_not_completed; status=blocked |
| 436 | 2026-08-13T17:38:00.029Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_MODEL_NOT_COMPLETED |
| 437 | 2026-08-13T17:38:00.142Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_MODEL_NOT_COMPLETED; failure_class=CANDIDATE_MODEL_NOT_COMPLETED |

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
- Events checked: `14`
- Chain head: `6cbb4fe492ad7c6585d1201806d44a6b6f3404a38efe1fbc73c588f0aad6e9ba`
