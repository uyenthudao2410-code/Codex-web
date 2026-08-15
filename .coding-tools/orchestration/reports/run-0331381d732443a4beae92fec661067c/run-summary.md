# Orchestration Run Summary

- Run: `0331381d732443a4beae92fec661067c`
- Task: `313d499cc31a4338b569f56aa67c89e4`
- Objective: Run the focused P0 causal-evaluation regression suite against the exact current dirty worktree. Do not mutate source unless a failing test requires a separately reasoned replan; this run is proof-only.
- Status: **accepted**
- Started: `2026-08-15T07:46:48.637Z`
- Finished: `2026-08-15T07:48:38.668Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f97ecc4a14c449f2b7d89ae01632b18f` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fac3eefb2d034ff2b8d9632ae7d94802 | f97ecc4a14c449f2b7d89ae01632b18f | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | 803e2cf4f5a396c016670bc695e79d2628789615424bc8f959ea18f9faf72ecf | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4812 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `f99a3e8b748fe3e4efcb04c66d8dabe269d65bc8c6ca927c126d497831388fbb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
