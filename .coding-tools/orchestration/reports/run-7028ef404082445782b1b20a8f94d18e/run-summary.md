# Orchestration Run Summary

- Run: `7028ef404082445782b1b20a8f94d18e`
- Task: `451c7dfce7674be695026dd971ac0788`
- Objective: Authoritatively prove the Windows CI path-identity repair after the prior fresh-stdio proof process was terminated by its 90-second background handoff. The frontend prerequisite and Rust build cache are now ready, and an out-of-band diagnostic rerun passed all 200 webcodex-cli tests.
- Status: **accepted**
- Started: `2026-08-13T06:16:50.452Z`
- Finished: `2026-08-13T06:21:16.119Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c399311794a740f9ba09066c9193e93a` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | replanned |
| 2 | `a25f98b4b1504a5fb4eb2090e67141f2` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | replanned |
| 3 | `09968a2d6cac4c5e8671982e1a6dd728` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4eecb55e4bcb4d9fbd47d2445a604184 | 09968a2d6cac4c5e8671982e1a6dd728 | accepted | deb03fc523f688b523aaa3a264c8954920450ccf |  | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 126 | `deterministic` | `deterministic` | explicit_request |
| 136 | `deterministic` | `deterministic` | explicit_request |
| 150 | `auto` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 130 | `RUNTIME_RESUME_REQUIRED` | `EXECUTING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 145 | `SOL_REJECTED` | `ACCEPTING` | Final review found the patch mutation landed in the primary dirty worktree while the isolated worktree used for proof remained clean. The 200/200 proof therefore does not cover the actual mutation target; reject and replan with explicit isolated-worktree mutation plus proof. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `88b2a71e1448f6d139d4b629e9865109e3114d0c9db273bff2ec7825e34aa03f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
