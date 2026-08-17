# Orchestration Run Summary

- Run: `d2845cd5070c4767b218049e1473fba7`
- Task: `461a027891794277b9e05b6e3e787f2e`
- Objective: Inspect the current unaccepted packaging-integrity WIP only. Do not modify files. Determine exactly what source changes now exist in scripts/verify-packaged-resources.js, scripts/packaged-recovery-smoke.js, tests/build-verification.test.js, package.json/build scripts, and any adjacent packaging files. Compare them to the intended fix: stale dist must not survive; packaged resources must be exact current-source identity; packaged Recovery smoke must detect stale/tampered resources. Preserve unrelated changes. This ChatWeb task does NOT authorize commit, push, release, install, Scheduled Task mutation, or service restart.
- Status: **aborted**
- Started: `2026-08-17T07:57:39.133Z`
- Finished: `2026-08-17T07:58:43.800Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `20fa8471c8cb44f9af27c6210468dd45` | `mcp_only` | `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf` | replanned |
| 2 | `efcf5ca0cbe04865934bfece1687d220` | `mcp_only` | `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 12305 | `deterministic` | `deterministic` | explicit_request |
| 12346 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 12334 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 12340 | `EXECUTION_OWNER_INVALID` | `PROVING` |  |
| 12362 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `2880c79e46f770f157f6149d05037a30cbb014ea6645e89d7ff45da3abd6f5f5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
