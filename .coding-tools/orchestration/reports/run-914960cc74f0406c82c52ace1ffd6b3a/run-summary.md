# Orchestration Run Summary

- Run: `914960cc74f0406c82c52ace1ffd6b3a`
- Task: `0434d82fa150496fae25ad5d4414cba9`
- Objective: Continue Layer C after accepted C1a on the current authoritative checkout. Wire explicit compute_placement_policy guards into run_readonly_validation and run_readonly_validation_agent; explicit selector only for long unsandboxed Agent-backed structured-job capable clean exact-source cargo_check/test. Implement local_only forcing source with no remote target selection and server_preferred using existing clean target selection/revalidation plus source fallback. Build ShellJobValidationComputePlacement from actual executor, persist it in ShellJobValidationMetadata and ValidationHandoff. Do not yet add tests in this wave beyond compile proof; selector absent must preserve current auto-offload behavior. Preserve all telemetry/concurrent commits. No analyzer/manifest/restart/P3 enrollment.
- Status: **accepted**
- Started: `2026-08-18T00:23:21.929Z`
- Finished: `2026-08-18T00:35:15.656Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `af55d1a28cc24c258acf1845cc46b33f` | `deep_single_lane` | `17e87d34b159cbc175a77bb041e670000c9f7f4b` | replanned |
| 2 | `0148adaac09140e39d50b7e2b1ebe1b7` | `mcp_only` | `17e87d34b159cbc175a77bb041e670000c9f7f4b` | replanned |
| 3 | `b8f926f426914df98de269bb09010c41` | `mcp_only` | `17e87d34b159cbc175a77bb041e670000c9f7f4b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 13931e17e80e4911914475787df46083 | b8f926f426914df98de269bb09010c41 | accepted | 17e87d34b159cbc175a77bb041e670000c9f7f4b | f3f98bfba35450a395e433dda0ded97edf8448e0f546e3588678f67b628616d4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16314 | `sol_xhigh` | `sol_xhigh` | explicit_request |
| 16360 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 16383 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16320 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |
| 16376 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `105`
- Chain head: `35dc75a3c181ef05008301c28a66e545f0d1f1626e437e6c88d18e4d60fcfe12`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
