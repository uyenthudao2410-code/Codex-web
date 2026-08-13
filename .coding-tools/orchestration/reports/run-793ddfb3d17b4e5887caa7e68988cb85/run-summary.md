# Orchestration Run Summary

- Run: `793ddfb3d17b4e5887caa7e68988cb85`
- Task: `d92a6a5912c84ea9a242e9c8909f91e2`
- Objective: Fix the confirmed Windows CI false rejection of DOS 8.3/case-equivalent credential paths on clean HEAD deb03fc5 in this isolated worktree only. Preserve the symlink/junction fail-closed boundary. The failing GitHub runner resolves C:\Users\RUNNER~1 to a long canonical user path, and stored project recovery similarly compares a canonical long path against a short-spelled requested path. Prepare an isolated repair; do not touch the primary dirty worktree.
- Status: **active**
- Started: `2026-08-13T06:21:43.676Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `25090446b63f415b82d40d0ba1c2f7a3` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | replanned |
| 2 | `cd870b14e8d34e509fa15df5025625a6` | `mcp_only` | `deb03fc523f688b523aaa3a264c8954920450ccf` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 163 | `auto` | `deterministic` | caller_supplied_change_set |
| 177 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 172 | `CHECK_FAILED` | `PROVING` |  |
| 185 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `268bf648dd8f5fc801bbddfd0b915b647416254302d154c9edd4afc925fefc2a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
