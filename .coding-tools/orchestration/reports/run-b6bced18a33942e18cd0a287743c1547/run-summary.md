# Orchestration Run Summary

- Run: `b6bced18a33942e18cd0a287743c1547`
- Task: `af66d61ea43d4e16ab50b3ec4954d650`
- Objective: Fix the demonstrated Windows artifact-to-npm smoke failure without weakening the production prepack/release-manifest guard. The smoke currently creates only a local file:// manifest in %TEMP% and then runs npm pack directly in npm/webcodex, whose prepack requires a publish-ready canonical manifest. Change only scripts/npm_install_windows_smoke.ps1 so it creates two manifests from the same real artifact SHA: (1) canonical GitHub release URL manifest staged into a tracked-source-only temporary npm package tree for release-manifest validation and npm pack, and (2) the existing local file:// manifest used only via WEBCODEX_MANIFEST for the offline installer. Stage package sources from the exact current commit with git archive, not by copying the workstation tree. Preserve the strict prepack check and all existing installer assertions/cleanup. Do not touch unrelated files.
- Status: **active**
- Started: `2026-08-13T17:55:17.411Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `4f38d165be614d7b9ea9d01bcdf5ec7e` | `mcp_only` | `bb8ccdcb87a13afc4c4d3a99b756cf821dfcfe72` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 480 | `auto` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `55a482306321f69b503faae50080c0c627c3da5b790917ffbb23cbf0815f84f7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
