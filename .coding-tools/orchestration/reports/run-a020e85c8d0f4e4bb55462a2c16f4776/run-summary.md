# Orchestration Run Summary

- Run: `a020e85c8d0f4e4bb55462a2c16f4776`
- Task: `0926b3663f15483e8c6e2241e54d5d1e`
- Objective: Implement the remaining Layer C of P3 validation compute-placement control on the authoritative current checkout. Consume the already-plumbed optional compute_placement_policy for cargo_check/cargo_test only. Explicit selector must reject before enqueue/process unless resolved project is Agent-backed, sandbox is absent, request is long structured validation (effective timeout > sync wait), Runner supports structured async validation handoff, and source is Clean exact-source with a valid exact git head. Unknown selector is already typed/serde rejected. Explicit local_only must force source Runner and never select/call server compute. Explicit server_preferred must use existing clean-source server target selection + revalidation and safe local fallback; caller never supplies runner id. Absent selector must preserve all current production behavior including dirty-snapshot auto-offload. For explicit runs construct ShellJobValidationComputePlacement evidence and persist it in ShellJobValidationMetadata, immediate cargo terminal/handoff result, and job_status/job_log validation projection; absent selector must keep evidence absent. Add focused tests for local_only, server_preferred success/fallback, invalid explicit contexts pre-execution, default absent-selector behavior, projection, and cargo_fmt/schema rejection as needed. Do not modify analyzer/frozen P3 manifest, do not restart runtime, do not enroll representative P3 pairs, and preserve all .coding-tools telemetry plus existing formatting diffs.
- Status: **accepted**
- Started: `2026-08-18T00:20:09.979Z`
- Finished: `2026-08-18T00:23:08.043Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `a9c7680dd0f44f46a479638f269d1187` | `mcp_only` | `189de19e2f7dbaa2a71ee62dbcc50d5d76a55c0a` | replanned |
| 2 | `7ae51200746b4f2285b9fdd8c1938177` | `mcp_only` | `17e87d34b159cbc175a77bb041e670000c9f7f4b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 189ab5dcf8ff49c090c1b6969105ae1e | 7ae51200746b4f2285b9fdd8c1938177 | accepted | 17e87d34b159cbc175a77bb041e670000c9f7f4b | 03d6060beffd13381548eb210d9c88c8324411c9fce48d70286434c0a02014d7 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16288 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16281 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `80f89457e4769c21bc819a46143fea080f6e565c1b7749ef49a9cf646495efc1`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
