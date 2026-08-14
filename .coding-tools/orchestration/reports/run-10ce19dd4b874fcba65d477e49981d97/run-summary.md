# Orchestration Run Summary

- Run: `10ce19dd4b874fcba65d477e49981d97`
- Task: `214f2ac819f94a1a83bbb16c5a190095`
- Objective: Implement P-MP2 OpenCode read-only Provider Adapter only. Add a bounded in-process adapter around `opencode run --model ... --format json --agent execution-hub-readonly --dir <workspace>` with prompt sent on stdin rather than argv, exact allowlist Flash/Pro, Job/process-group lifecycle, start/observe/cancel/timeout, bounded stdout text extraction, session correlation, prompt hash/bytes only, and fail-closed side-effect detection. Force a highest-priority inline OpenCode config with global and agent-specific wildcard deny, allowing only read/glob/grep/list/lsp, so edit/bash/task/web/external/custom/MCP tools are denied. Integrate authenticated internal /__control/hub provider_dispatch/provider_observe/provider_cancel restricted to electron-panel/electron and current task-projected eligible run/wave. Create/update canonical external delegation without storing raw prompt/output; correlate later OpenCode message.updated telemetry to the adapter delegation via session id. Make canonical usage_event recording idempotent so late measured telemetry can attach after an adapter terminal transition. No shadow routing in this run. Preserve Smart-v3 8 tools/current routing/controller roles/UI. Do not restart services/change settings/run paid provider inference/commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-08-14T09:44:43.890Z`
- Finished: `2026-08-14T09:47:57.408Z`

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
| 1 | `6fb34a23b68c4571ba2214912a17f56e` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `5e2c7639160a41678a5fb566159ba0e1` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 3 | `a89534dd928a4a89a5710648edbcbb07` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 5d539f294f7047699b50b930e76c7063 | a89534dd928a4a89a5710648edbcbb07 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | c56162a6fd442e9db91e362fa2998356c071d62196ca033ffdd01fc879ae8689 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1769 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1779 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1789 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1773 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 1783 | `PATCH_FAILED` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `ee8cc004e9786bf67c9747af4f6e22f058ab2c0fd35aba2e9090d46ad078f03e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
