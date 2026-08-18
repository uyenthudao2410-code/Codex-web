# Orchestration Run Summary

- Run: `e5a7212244414e3aacade09b53bd9397`
- Task: `dccbc6643f00466385a9fd39ba313556`
- Objective: Prepare a Git commit/push of the entire current E:\DEV\Codex-web worktree to origin/main, preserving all project and .coding-tools data, with exactly two permanent exclusions: .coding-tools/orchestration/ledger.sqlite3-shm and .coding-tools/orchestration/ledger.sqlite3-wal. Determine whether those two files are tracked or ignored already and inspect the current .gitignore so the exclusions can be made persistent without excluding ledger.sqlite3 itself.
- Status: **accepted**
- Started: `2026-08-18T11:30:07.953Z`
- Finished: `2026-08-18T11:33:29.452Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `cce417a7eacc47989140aed6a6039c4b` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 2 | `a4db8ed2172347e88e9492367344507e` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 3 | `6d37df8880af4e359efd78074eac26fa` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 61a2eb3ba42e4171a167954762c254e5 | 6d37df8880af4e359efd78074eac26fa | accepted | 128afd79a1dfe2b607de4ec519a053a2ab050d0f | bbe477e0b1ecd8471c9ec336cf220dd15724f6b2ad209096f1d4ff5709c922dd | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 17444 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 17461 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 17437 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 17455 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `027b461133f8447f7ca98d3d50667825fbe29a34abb66b5ab2513a62cd965429`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
