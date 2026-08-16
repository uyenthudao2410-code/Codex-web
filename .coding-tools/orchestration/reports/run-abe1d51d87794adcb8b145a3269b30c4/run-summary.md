# Orchestration Run Summary

- Run: `abe1d51d87794adcb8b145a3269b30c4`
- Task: `7e891c98dc464868b7f5087e99939504`
- Objective: Recover R2A A2 after patch ambiguity. Read only the unique current contexts in crates/webcodex-runner/src/main.rs around: validation source metadata extraction after validation plan check; the first validation process spawn immediately after job slot reservation; worker captures before thread spawn; subsequent validation-step spawn; and final terminal update. Also confirm whether any A2 edits were partially applied (they should not have been). No mutation.
- Status: **accepted**
- Started: `2026-08-16T12:01:23.440Z`
- Finished: `2026-08-16T12:06:19.081Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `0cdb251609464e418e4e04fca229a203` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `924029695a514a3083b38ee291c37c33` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 3 | `78a6e294a40e420a8376eb34623cf8c4` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 8fe7a8e8ea4b42e291147f9e00c63995 | 78a6e294a40e420a8376eb34623cf8c4 | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | 3f909df66c35048b5938899550d406d089a7e17a93a73c88c994afc53a4c0972 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 7748 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 7759 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 7771 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 7752 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 7763 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `57`
- Chain head: `51339c3edbfa2ca040f9fe034166e2f58a5edbcd76e54d83f8adbff6918bb790`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
