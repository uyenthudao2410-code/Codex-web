# Orchestration Run Summary

- Run: `aed8c7100d7d4a80be161e7571077a65`
- Task: `f433b337c4744fef9ee4b10c658369e1`
- Objective: Close the final pre-P3 preregistration analysis gap without starting any P3 treatment. Generalize the existing compare_route_policies CLI so it accepts arbitrary explicit policy identifiers while keeping mini/luna as defaults when omitted, and add focused regression proving the generic paired-policy evaluator accepts LOCAL_FIRST_V1 versus SERVER_FIRST_DETERMINISTIC_V1 with exact representative pair identity. Do not change ledger semantics, public MCP schema, routing authority, automatic activation, or run any representative P3 treatment.
- Status: **accepted**
- Started: `2026-08-17T19:56:17.017Z`
- Finished: `2026-08-17T19:57:47.297Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ffb53a382c554bada1e4a3a259b98333` | `mcp_only` | `bc07e240740726d9a5ddbd590e01568344a92440` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 646274209f734ba7b396ccbfe2913aaa | ffb53a382c554bada1e4a3a259b98333 | accepted | bc07e240740726d9a5ddbd590e01568344a92440 | e438083c5b379c8d983bc96a1b8e9d53180f961be9a0564fe25ca95e187238af | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15686 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `a5f7004415ce1408666ea50aea7652a1d91cfec2bb26e775dfcfb666a606b77e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
