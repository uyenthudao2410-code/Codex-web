# Orchestration Wave 1

- Run: `10ce19dd4b874fcba65d477e49981d97`
- Wave: `6fb34a23b68c4571ba2214912a17f56e`
- Objective: Implement P-MP2 OpenCode read-only Provider Adapter only. Add a bounded in-process adapter around `opencode run --model ... --format json --agent execution-hub-readonly --dir <workspace>` with prompt sent on stdin rather than argv, exact allowlist Flash/Pro, Job/process-group lifecycle, start/observe/cancel/timeout, bounded stdout text extraction, session correlation, prompt hash/bytes only, and fail-closed side-effect detection. Force a highest-priority inline OpenCode config with global and agent-specific wildcard deny, allowing only read/glob/grep/list/lsp, so edit/bash/task/web/external/custom/MCP tools are denied. Integrate authenticated internal /__control/hub provider_dispatch/provider_observe/provider_cancel restricted to electron-panel/electron and current task-projected eligible run/wave. Create/update canonical external delegation without storing raw prompt/output; correlate later OpenCode message.updated telemetry to the adapter delegation via session id. Make canonical usage_event recording idempotent so late measured telemetry can attach after an adapter terminal transition. No shadow routing in this run. Preserve Smart-v3 8 tools/current routing/controller roles/UI. Do not restart services/change settings/run paid provider inference/commit/push/release/deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `d13d9e9e1b50b1f07c213597dc6878e0947813061415022a467d5fe2b7f655f4`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1765 | 2026-08-14T09:44:44.209Z | run_started |  | PREFLIGHT |  |
| 1766 | 2026-08-14T09:44:44.655Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1767 | 2026-08-14T09:44:44.851Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1768 | 2026-08-14T09:44:45.291Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1769 | 2026-08-14T09:44:45.447Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1770 | 2026-08-14T09:44:45.600Z | state_transition | READY | ROUTED | reason=route_selected |
| 1771 | 2026-08-14T09:44:46.126Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cd96b5d04238455fa72f6e7b52a5a670 |
| 1772 | 2026-08-14T09:44:46.320Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1773 | 2026-08-14T09:44:46.760Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1774 | 2026-08-14T09:44:47.068Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=cd96b5d04238455fa72f6e7b52a5a670 |
| 1775 | 2026-08-14T09:44:47.232Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
