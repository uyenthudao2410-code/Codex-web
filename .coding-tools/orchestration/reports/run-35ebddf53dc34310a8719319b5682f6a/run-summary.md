# Orchestration Run Summary

- Run: `35ebddf53dc34310a8719319b5682f6a`
- Task: `8aee24c3a163426d9a75236e726a9a1f`
- Objective: Verify the live EOCL control loop with a no-write command and record deterministic proof only.
- Status: **accepted**
- Started: `2026-08-13T05:44:06.056Z`
- Finished: `2026-08-13T05:45:03.926Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f8662ab49a694ced90207fa7c41c6922` | `deep_single_lane` | `bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8` | replanned |
| 2 | `47403316f794449cbbe2964d6f946578` | `mcp_only` | `bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| a7bc03ad23e14a78a115cfdd910af125 | 47403316f794449cbbe2964d6f946578 | accepted | bd87d8bc5c2b1c25f9f9fe5fe3dcb46b29e78fe8 | bc2374ac9db7b9386aa89204ae9e1ba03f15e9f65d18a6ed4750cf0102b19254 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 76 | `auto` | `sol_xhigh` | deep_or_broad_context |
| 87 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 80 | `CANDIDATE_SCOPE_MISSING` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `a3864601bd463df26adc4b16ba6d0749dc4331410c32b2095ddf03ab4dbd603b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
