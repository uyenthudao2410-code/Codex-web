# Orchestration Run Summary

- Run: `bd3fa859b53c47978b6a2d973b76fa49`
- Task: `7361b3270d7048eb8e262ac9014a8839`
- Objective: P1 activation repair 3: make host-visible turn measurement causally gated by a post-injection user send intent, so page reload/hydration/current in-progress turns can never create a span. Do not read prompt/response content. Detect composer intent only structurally via composer form submit, data-testid send-button click, or unmodified Enter on textarea/contenteditable; ignore IME composition. After intent, accept only the newest structurally visible tail user turn, then the newest tail assistant turn, with stable conversation-turn ordinal monotonicity when available. Keep the baseline priming as an additional guard. Bump current host evidence to schema v4 so v1-v3 smoke artifacts are preserved but excluded. Preserve all clock-domain and no-proximity-correlation rules; no routing/benchmark/promotion changes.
- Status: **accepted**
- Started: `2026-08-15T08:46:19.524Z`
- Finished: `2026-08-15T08:50:39.101Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `bc78c25c92764977b7066eef5379d4ad` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6bdd0e55d73440fb98959228066e064c | bc78c25c92764977b7066eef5379d4ad | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | e5e284e2038ba3dd1b4f6b03ee8cf2a13f5555a75033b195fd963ae8414ea72b | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5024 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `122aed87cadc5206ba8d055976400cf00dbd9cd3780463208711ad4707c166c7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
