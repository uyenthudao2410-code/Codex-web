# Orchestration Run Summary

- Run: `09b7d005ea0d42d3823da3ab4f52a0f9`
- Task: `4f198b3f087046fc813346c9ffdaf412`
- Objective: Fresh H4 Codex exact-usage runtime canary only. Read the current usage persistence path in resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py and resources/coding-tools-mcp/coding_tools_mcp/agent_candidate.py, then report whether complete non-negative integer inputTokens/cachedInputTokens/outputTokens/reasoningOutputTokens from Codex App Server thread/tokenUsage/updated are mapped to a provider UsageEvent. Do not patch, write, adopt, restart, commit, or change source. The purpose is to trigger one bounded Codex candidate lane and then inspect whether exact X/Y/Z/R usage is durably attributed to this RUN/WAVE/delegation.
- Status: **aborted**
- Started: `2026-09-03T06:52:51.246Z`
- Finished: `2026-09-03T06:55:31.741Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `3a2d000950864852b3149870ad2abb6f` | 1 | `run_initial_objective` | `bounded_candidate` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `0598434481034eccb01768a561d6de92` | 2 | `replan_request` | `bounded_candidate` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36521 | `mini` | `mini` | explicit_request |
| 36538 | `mini` | `mini` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 36528 | `PROMPT_TOO_LARGE` | `ROUTED` |  |
| 36546 | `CANDIDATE_REPORTED_BLOCKED` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `85e931be8e82fa7e53c9650f041eb6fb64c40f26fcabc967c6a15ec59685d9b7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
