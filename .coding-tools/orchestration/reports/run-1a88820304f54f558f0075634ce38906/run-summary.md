# Orchestration Run Summary

- Run: `1a88820304f54f558f0075634ce38906`
- Task: `2aaeec2e70974ef4b0b3cc1b71a9ff43`
- Objective: Complete the extracted Runtime mixin regression repair. Restore workflow_tools dependencies that existed in the pre-extraction Runtime: parse_patch, RunContext, AGENT_EXECUTION_ROUTES, EVALUATION_SCHEMA_VERSION, and the host-correlation constants used by AgentWorkflowMixin. Preserve behavior and public contract.
- Status: **active**
- Started: `2026-08-15T10:24:37.774Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `67c4861d5e0b473b8626a51865a19ca5` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | replanned |
| 2 | `4751d16b595f4d539fb9929db698edac` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5223 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 5236 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5231 | `CHECK_FAILED` | `PROVING` |  |
| 5251 | `SOL_REJECTED` | `ACCEPTING` | Broad Python MCP validation found 18 extraction regressions despite focused idempotency passing: missing coordination/context/workflow dependencies, lost organic host-turn claim/binding behavior, lost public continuation scope forwarding, and missing server compatibility re-exports for candidate/review constants. Do not checkpoint until these are restored and the full suite passes. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `d3ba54d2c859d5ea52ef8187ae93d0ab4ac742829613c3d4c88f4006c592ac83`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
