# Orchestration Run Summary

- Run: `a2f3ab42a4ab408ea7350eddaf952933`
- Task: `83f7cb6a84714345b39fa74713f83e02`
- Objective: Implement the prepared L3E controller quantification without contaminating canonical exact accounting. Add a content-free controller_token_estimate projection to accepted-result operations analytics. For accepted RUNs missing exact controller UsageEvents, use empirical exact-controller-total-token/model_visible_bytes ratios when at least 5 positive exact calibration pairs exist, returning measurement=CALIBRATED_ESTIMATE, p10/p50/p90 missing-controller total-token estimate, confidence, calibration sample count, and provenance. When fewer than 5 calibration pairs exist but missing accepted RUNs have positive model_visible_bytes, return a separate measurement=CONTEXT_ESTIMATE using the existing explicit context-estimate prior semantics (2-6 bytes/token interval, p50=4 bytes/token), label it LOW confidence and not_controller_total=true; never call this controller total. If evidence is insufficient return UNKNOWN/unknown_not_zero. Exact UsageEvents always remain authoritative and no estimate is written into usage_analytics/ledger/cost. Wire renderer dashboard trust strip to show exact, calibrated missing-controller estimate, or context estimate numerically with interval/confidence; keep six canonical KPI totals exact and unchanged. Technical provenance remains in analytics but not surfaced on default Overview. Add focused Python behavior tests plus dashboard contract assertions. Do not restart runtime, modify ledger schema/controller ingress/Electron journal, commit, push, release, or deploy.
- Status: **accepted**
- Started: `2026-09-04T00:54:27.213Z`
- Finished: `2026-09-04T00:59:00.703Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `aedf53c1ab164ac5835e90289d6b853f` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 2 | `ce13e273dabb4a449d34bd90107309a6` | 1 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 3 | `ada0489eff8542959767dd03f6610a07` | 1 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 4 | `2316febe2b2d471ba265092652641657` | 2 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6cac40c537824515be9b05ac3d250af0 | 2316febe2b2d471ba265092652641657 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 4603208631d412174c1de321cd4331b79e13ed637f9caa598b6469b30bbe5516 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 39178 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 39205 | `deterministic` | `deterministic` | explicit_request |
| 39227 | `deterministic` | `deterministic` | explicit_request |
| 39261 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 39198 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 39220 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 39254 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance is procedurally blocked by ACCEPTANCE_FILE_ATTESTATION_REQUIRED because the four accepted paths were pre-existing dirty relative to the authoritative worktree. Source semantics and proof are accepted, but durable exact-byte adoption provenance must be recorded before checkpoint. Replan to an adoption-only corrective wave on the same current SHAs; no content changes. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `116`
- Chain head: `5376c3d7fa2375e155d9985cb045c5ae3b61d89c934de589dbdae996684e022c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
