# Orchestration Run Summary

- Run: `81b49c06d3904675ad10d5757ffff6f8`
- Task: `f0d13ce16cab41bfbcf23e7c5ac29c0e`
- Objective: Fix the confirmed WEBCODEX_MCP_MODEL_SURFACE cross-test race in src/mcp_tests.rs only. Ordinary test_runtime() must be deterministic LocalCoding and never read process env. Normal full-operator MCP tests must inject ModelSurface::FullOperatorRuntime explicitly (helper is fine). Add a separate test_runtime_from_env() that resolves process env and use it only in tests explicitly validating env-driven model-surface selection/immutability; those tests must hold admin_cli::TEST_ENV_LOCK and restore/remove the env variable. Remove full_operator_mcp_env/full_operator_mcp_env_locked from ordinary tests and delete them if no longer needed. Preserve TEST_ENV_LOCK around WEBCODEX_MCP_COMPACT_SCHEMAS mutations. Do not change production code, OAuth/MCP authorization, or model-facing tool sets. Verify cargo fmt --check and focused Rust tests for oauth2_mcp_tools_list_requires_runtime_read, explicit_local_coding_v1_selects_local_coding, explicit_full_operator_v1_reports_full_operator_surface, and selected_surface_is_immutable_after_environment_changes. Finally verify every MCP_MODEL_SURFACE_ENV mutation in src/mcp_tests.rs is lock-protected and no ordinary runtime construction depends on model-surface env.
- Status: **active**
- Started: `2026-08-13T17:37:24.193Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `038c1990a6f4484d869fc95947ad786e` | `deep_single_lane` | `db7725e3601afc2692627a0b4eef674d599bd17e` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 430 | `auto` | `sol_xhigh` | deep_or_broad_context |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 436 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `6cbb4fe492ad7c6585d1201806d44a6b6f3404a38efe1fbc73c588f0aad6e9ba`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
