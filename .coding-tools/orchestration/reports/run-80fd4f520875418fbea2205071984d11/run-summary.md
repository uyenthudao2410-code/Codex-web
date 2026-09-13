# Orchestration Run Summary

- Run: `80fd4f520875418fbea2205071984d11`
- Task: `5cfc5996831b430cbe2fbef4c3ca6150`
- Objective: Resolve Problem prl-semantic-localization-provider-health-20260912 revision 1 with the localized causal repair. Normalize absolute caller semantic scopes to project-relative only when the resolved target is inside the bound workspace; keep outside/traversal/NUL scopes fail-closed. Add truthful effective semantic provider health that distinguishes configured binding from executable resource health, and use it for full workspace_context capability reporting. Preserve existing semantic-first admission and bounded text fallback; do not weaken HEAVY concurrency/host-pressure guards and do not modify the Rust bridge. Add focused regression tests for absolute-in-workspace normalization, outside rejection, configured-but-unhealthy truthful reporting, bounded text fallback, and healthy semantic handling. Preserve unrelated dirty WIP. No restart, commit, push, clean, reset, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-12T11:50:37.253Z`
- Finished: `2026-09-12T14:05:34.854Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **4**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f3ff3ae3dbc0449496a1696c1f879fbf` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `35f014514ac846f1a63e4ae1d94769d9` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `9bf15639ebeb4b33a206fc0b926aacfb` | 3 | `replan_request` | `mcp_only` | `` | replanned |
| 4 | `a1e01a838bec44db99272f884dcca326` | 3 | `replan_request` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | replanned |
| 5 | `bed148a76b76444f9840735e04e8eca3` | 4 | `replan_request` | `mcp_only` | `228b91e6128479d4b3699e622d4f51dd431acb24` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ff7f767ab89a4a419142f84a5e3f4cd2 | bed148a76b76444f9840735e04e8eca3 | accepted | 228b91e6128479d4b3699e622d4f51dd431acb24 | 2c29edd88e01df1e4a8d62a9cfcbe47ae046a2a13b587e3dde3716568aa8a3ac | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51899 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 51930 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 52166 | `deterministic` | `deterministic` | explicit_request |
| 52195 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 51919 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 52135 | `SOL_REJECTED` | `ACCEPTING` | Regression oracle is green, but full_problem exact-wave coverage is incomplete because the required live native-semantic known-symbol and measurement_recovery evidence was obtained after activation in a different diagnostic wave. Replan the same RUN to capture live semantic handling and rerun the focused regression oracle in one canonical wave without further source changes. |
| 52142 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 52184 | `SOL_REJECTED` | `ACCEPTING` | Fresh regression proof d858527417974fc4bfa4dcb3e6896dcb passed, but this wave cannot satisfy full_problem closure because its initial live semantic preflight recorded SEMANTIC_PROVIDER_CALL_FAILED while the external semantic sidecar was down. The sidecar is now restored. Replan the same canonical RUN for a final wave whose preflight starts healthy, records semantic_handled >= 1 with zero text fallback, and then runs a fresh focused regression proof. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `139`
- Chain head: `016a500b3c49003bd430657c6775f289598ec0bd9fa862541bfa1fd281abe16b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
