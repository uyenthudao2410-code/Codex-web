# Orchestration Wave 2

- Run: `10ce19dd4b874fcba65d477e49981d97`
- Wave: `5e2c7639160a41678a5fb566159ba0e1`
- Objective: Implement P-MP2 OpenCode read-only Provider Adapter only. Add a bounded in-process adapter around `opencode run --model ... --format json --agent execution-hub-readonly --dir <workspace>` with prompt sent on stdin rather than argv, exact allowlist Flash/Pro, Job/process-group lifecycle, start/observe/cancel/timeout, bounded stdout text extraction, session correlation, prompt hash/bytes only, and fail-closed side-effect detection. Force a highest-priority inline OpenCode config with global and agent-specific wildcard deny, allowing only read/glob/grep/list/lsp, so edit/bash/task/web/external/custom/MCP tools are denied. Integrate authenticated internal /__control/hub provider_dispatch/provider_observe/provider_cancel restricted to electron-panel/electron and current task-projected eligible run/wave. Create/update canonical external delegation without storing raw prompt/output; correlate later OpenCode message.updated telemetry to the adapter delegation via session id. Make canonical usage_event recording idempotent so late measured telemetry can attach after an adapter terminal transition. No shadow routing in this run. Preserve Smart-v3 8 tools/current routing/controller roles/UI. Do not restart services/change settings/run paid provider inference/commit/push/release/deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `726c84c0445d8d6f7819e3a77ed2cd8eaf46448da8c34dcf250c6a7f3da92197`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1776 | 2026-08-14T09:46:48.768Z | wave_replanned |  | PREFLIGHT | reason=The previous P-MP2 run failed before patch application because a broad multi-file server patch had ambiguous context. Materially narrow the strategy: first implement the provider adapter as an isolated module with fake-process tests and no server integration; checkpoint it before a separate integration run. |
| 1777 | 2026-08-14T09:46:48.919Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1778 | 2026-08-14T09:46:49.101Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1779 | 2026-08-14T09:46:49.267Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1780 | 2026-08-14T09:46:49.417Z | state_transition | READY | ROUTED | reason=route_selected |
| 1781 | 2026-08-14T09:46:49.978Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e93ac4b4c0f54a1b9833765107974ff1 |
| 1782 | 2026-08-14T09:46:50.125Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1783 | 2026-08-14T09:46:50.580Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_FAILED |
| 1784 | 2026-08-14T09:46:50.876Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=e93ac4b4c0f54a1b9833765107974ff1 |
| 1785 | 2026-08-14T09:46:51.101Z | state_transition | EXECUTING | REPLAN | reason=PATCH_FAILED; failure_class=PATCH_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `ee8cc004e9786bf67c9747af4f6e22f058ab2c0fd35aba2e9090d46ad078f03e`
