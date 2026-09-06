# Orchestration Run Summary

- Run: `9fb216f2c27742be9a15a785b144a8b1`
- Task: `f921d55ec2d9467f92111a6d6a0a2c5f`
- Objective: Finalize token dashboard hierarchy without changing token accounting: rename the canonical provider UsageEvent tile from the ambiguous TỔNG TOKEN label to TOKEN PROVIDER, preserve TOKEN CHATWEB as the primary per-turn/session structural measurement, and strengthen the regression test so renderChatTurnCard cannot depend on provider measured data or provider tile IDs. Preserve the existing local ChatWeb hero-card styling exactly.
- Status: **accepted**
- Started: `2026-09-04T11:17:29.217Z`
- Finished: `2026-09-04T11:31:49.825Z`

## Outcome metrics

- Waves: **7**
- Route decisions: **7**
- Failures observed: **6**
- REPLAN transitions: **6**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `645c06f11d934b169f449d7fda720a9f` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 2 | `32cd73ac92d54f2ca1f31becc264b39f` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 3 | `f8330e79a9b0490daa4b97bf870bf99e` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 4 | `2d458753453a463993481ef1900a4466` | 2 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 5 | `a5f2ac2bd26f416ea3b60861860522e4` | 3 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 6 | `e6c2fbabc3e9402fba6a8d61eb34761d` | 4 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 7 | `c1c9c44105c04329b56c7691aa311924` | 5 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2c41456d21c1453db50c44a17b119ac6 | c1c9c44105c04329b56c7691aa311924 | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 5c7d320dc20c714236be238e2b311534fed0ac813d42f7ace3f1f4a4b6c370cd | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 39558 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 39568 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 39596 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 39628 | `deterministic` | `deterministic` | explicit_request |
| 39638 | `deterministic` | `deterministic` | explicit_request |
| 39670 | `deterministic` | `deterministic` | explicit_request |
| 39684 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 39561 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |
| 39589 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 39621 | `SOL_REJECTED` | `ACCEPTING` | Acceptance provenance gap only: two pre-existing dirty acceptance paths were not durably adopted inside the final wave. Code and proof are green. Replan to an exact-byte no-write adoption wave for the current dashboard slice, then rerun the same proof and accept on that exact fingerprint. |
| 39631 | `BASE_DRIFT` | `ROUTED` |  |
| 39663 | `SOL_REJECTED` | `ACCEPTING` | Post-proof concurrent UI drift changed renderer/index.html and renderer/dashboard.css after the exact-byte adoption/proof. The new changes are compatible (ChatWeb hero/live styling and turn log) and preserve TOKEN CHATWEB -> TOKEN PROVIDER hierarchy, but accepting stale proof would be invalid. Replan to adopt and reprove the exact current UI bytes without removing or overwriting those concurrent enhancements. |
| 39676 | `ACCEPTANCE_FILE_SHA_MISMATCH` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `cbf6c2dfc1b6de0191bf136d8dd5f29df9d039e6bdeb25ceb3781f197810bfdb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
