# Orchestration Run Summary

- Run: `6271ce0c1edf4c478508f9759901fe84`
- Task: `7c92a8d397b64f56a27a7e7b188538b7`
- Objective: Fix the pre-existing Windows runner test-harness inconsistency exposed by the broad current-head suite. The production platform policy intentionally uses USERPROFILE and ignores HOME on Windows. Update only crates/webcodex-runner/src/main_tests.rs so the empty-allowed-roots default test derives the expected platform home through agent_init::home_allowed_root(), and make the three shared TEST_ENV_LOCK acquisitions poison-tolerant so one assertion cannot cascade into unrelated failures. Do not change production home/path policy or Wave A/B/C behavior. Preserve unrelated runtime evidence and local commits.
- Status: **accepted**
- Started: `2026-08-22T11:52:28.708Z`
- Finished: `2026-08-22T12:29:17.006Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `1886b1f3b7f744df9a8c502e928c963e` | 1 | `run_initial_objective` | `mcp_only` | `d15983737106fb33595b75bba01e718cefaf3682` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 742585470a7f427f8a743fe2d43b53e0 | 1886b1f3b7f744df9a8c502e928c963e | accepted | d15983737106fb33595b75bba01e718cefaf3682 | 896e8f596af8f704bb8264a07e371730a1e0c593eacc9e213048569819f37d57 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 27130 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `4541e44a897853dbf91498abbca23662729d2d4578644cef024a271964f3ab6c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
