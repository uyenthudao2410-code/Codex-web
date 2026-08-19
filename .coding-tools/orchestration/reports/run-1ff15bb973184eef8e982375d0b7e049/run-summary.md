# Orchestration Run Summary

- Run: `1ff15bb973184eef8e982375d0b7e049`
- Task: `f43a252e77b9478385e1fc6bb2c9071e`
- Objective: Fix webcodex ops explicit bearer-token source ambiguity. On clean current source, require at most one of --token, --token-file, or --env-file for ops status/agents/projects/smoke-preflight; preserve WEBCODEX_TOKEN environment fallback when none is explicitly selected. Add the smallest deterministic parser regression test covering both common ops and smoke-preflight. Do not modify files in prepare.
- Status: **accepted**
- Started: `2026-08-18T18:40:12.895Z`
- Finished: `2026-08-18T18:48:44.042Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `49eaa53cb98b4981b56d8bf473827bb9` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | replanned |
| 2 | `27c8738d5ed44cef859f2d281d6db18c` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7e148fffcb0d4b73be0d31b6667f5f51 | 27c8738d5ed44cef859f2d281d6db18c | accepted | b7af2598297870e816dd131b0f73e0f77d7608d5 | 63041cfcabf98d9522a6a75691d3c56e9c33007eb848e2d594c36188b04aef22 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 18108 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 18131 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 18125 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `53`
- Chain head: `b9325ca0cbb760ecdc48a551ccbc9ecbae66f84c7efb6135688925c7b1226782`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
