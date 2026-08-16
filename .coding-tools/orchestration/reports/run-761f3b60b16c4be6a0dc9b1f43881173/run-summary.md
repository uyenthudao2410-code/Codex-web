# Orchestration Run Summary

- Run: `761f3b60b16c4be6a0dc9b1f43881173`
- Task: `98376b144e0c40808317f73578fee70d`
- Objective: Run the focused R2B behavior oracle on the current already-compiled source without modifying files. Execute all tests whose names contain server_first_ with one test thread. Acceptance requires the command exit 0 and output demonstrating the new server-first tests actually ran (not zero tests): distinct opted-in exact target dispatch, source runner never selected as compute target, ineligible candidates fall back to source, and offload scope excludes cargo_fmt/short/sandboxed validation. Then run runtime_status_agent_summary_includes_protocol_version to validate observability reports server_preferred/dispatch_enabled=true. Do not run the full test suite and do not mutate source.
- Status: **aborted**
- Started: `2026-08-16T13:17:06.105Z`
- Finished: `2026-08-16T13:28:31.527Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2dd31a4c8b234b07be9c1b8525949dec` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8392 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `061bb15cd0fc8a14707776f4b86c743e1c63cb504a7f65893e8491fe62347d4d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
