# Orchestration Run Summary

- Run: `6cd0fdf7425c474491e7da37bcbe527d`
- Task: `d7b2d52c5acc4339a73d1d4c55487a1d`
- Objective: Diagnose exactly one genuine bug in the clean project_entry boundary that is independently fixable and has a focused deterministic oracle. Do not mutate source. Inspect src/project_entry.rs and src/project_entry_tests.rs plus only directly relevant setup/share helpers. Look specifically for mismatches between parse_options/readiness/remote_probe/render semantics and their tests or reachable runtime behavior. Exclude speculative style issues. Return the exact causal symbol, a concrete failing/reproduction test that should fail on current code, smallest causal file set, and confirm those source files are currently clean. If no genuine defect is provable, say so rather than inventing one. Keep P5 closed.
- Status: **aborted**
- Started: `2026-08-18T23:26:25.497Z`
- Finished: `2026-08-18T23:29:03.390Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `c7fe44d8e2424dfb8cd43c02d90750af` | `mcp_only` | `b7af2598297870e816dd131b0f73e0f77d7608d5` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `6`
- Chain head: `ad8621ec40abd3479da50d79215f17a3f8b2aba7b6e1db2ce61aaa0eb27e65d0`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
