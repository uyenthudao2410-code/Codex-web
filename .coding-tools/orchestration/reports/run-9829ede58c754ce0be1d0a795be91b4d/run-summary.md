# Orchestration Run Summary

- Run: `9829ede58c754ce0be1d0a795be91b4d`
- Task: `d5d1cc665d3e47ec92d7089ae320aa1d`
- Objective: Re-enter PREFLIGHT in the existing R2B run after the invalid no-op retained-output attempt. No source inspection is required; the next step will consume the retained rustfmt command output directly via command_control.
- Status: **accepted**
- Started: `2026-08-16T13:06:26.506Z`
- Finished: `2026-08-16T13:09:11.491Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `9cb7828069724b28a7f49a865230a8bc` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `b908fb7fc59442aa80d5f7d7e49863f0` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 3 | `700b5eef8bfe4989bfbf5f86a2cc8587` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 4 | `c607405fd864448986de9973d6445676` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 5 | `3ffc0cd84b4d48dc8fe2424eee5cb166` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 39030f14d6304f0f825c00d6b04a02e3 | 3ffc0cd84b4d48dc8fe2424eee5cb166 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | f02832f378ba018b898fe57947285af6192f2237d0381753f94963c1c50291d9 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 8217 | `deterministic` | `deterministic` | explicit_request |
| 8235 | `deterministic` | `deterministic` | explicit_request |
| 8253 | `deterministic` | `deterministic` | explicit_request |
| 8267 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8285 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 8228 | `CHECK_FAILED` | `PROVING` |  |
| 8246 | `CHECK_FAILED` | `PROVING` |  |
| 8257 | `INVALID_ARGUMENT` | `EXECUTING` |  |
| 8278 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `89`
- Chain head: `5f57cfc2d0c9ccddb6e14954c864afc489120b616fec045c8bccdf7253d58b0f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
