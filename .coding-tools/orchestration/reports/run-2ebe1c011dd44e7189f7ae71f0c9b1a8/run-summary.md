# Orchestration Run Summary

- Run: `2ebe1c011dd44e7189f7ae71f0c9b1a8`
- Task: `8ccb302b21ac45efb0466dbf43998f81`
- Objective: Make the Ubuntu canonical Rust gate diagnosable without weakening it. Preserve the exact cargo test --locked --workspace command and its exit status, tee its complete output to cargo-test.log, write a compact failure excerpt to GITHUB_STEP_SUMMARY / GitHub error annotations when it fails, and upload cargo-test.log as a short-retention artifact only on failure. This is release-proof observability so the exact failing Rust test/panic can be retrieved on the next CI run. Do not change Rust code or test selection.
- Status: **active**
- Started: `2026-08-13T17:56:11.034Z`
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
| 1 | `e9bf0f3b730f4dc89bfae20dfe6bdfb1` | `mcp_only` | `bb8ccdcb87a13afc4c4d3a99b756cf821dfcfe72` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 495 | `auto` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `afbf1e7234e387bcb92f183978167e7fa5caedbee8e3c586527dc0cdf45d551a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
