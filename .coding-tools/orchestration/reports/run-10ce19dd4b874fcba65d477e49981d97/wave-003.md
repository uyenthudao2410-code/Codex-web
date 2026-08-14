# Orchestration Wave 3

- Run: `10ce19dd4b874fcba65d477e49981d97`
- Wave: `a89534dd928a4a89a5710648edbcbb07`
- Objective: Implement P-MP2 OpenCode read-only Provider Adapter only. Add a bounded in-process adapter around `opencode run --model ... --format json --agent execution-hub-readonly --dir <workspace>` with prompt sent on stdin rather than argv, exact allowlist Flash/Pro, Job/process-group lifecycle, start/observe/cancel/timeout, bounded stdout text extraction, session correlation, prompt hash/bytes only, and fail-closed side-effect detection. Force a highest-priority inline OpenCode config with global and agent-specific wildcard deny, allowing only read/glob/grep/list/lsp, so edit/bash/task/web/external/custom/MCP tools are denied. Integrate authenticated internal /__control/hub provider_dispatch/provider_observe/provider_cancel restricted to electron-panel/electron and current task-projected eligible run/wave. Create/update canonical external delegation without storing raw prompt/output; correlate later OpenCode message.updated telemetry to the adapter delegation via session id. Make canonical usage_event recording idempotent so late measured telemetry can attach after an adapter terminal transition. No shadow routing in this run. Preserve Smart-v3 8 tools/current routing/controller roles/UI. Do not restart services/change settings/run paid provider inference/commit/push/release/deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `726c84c0445d8d6f7819e3a77ed2cd8eaf46448da8c34dcf250c6a7f3da92197`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1786 | 2026-08-14T09:47:34.759Z | wave_replanned |  | PREFLIGHT | reason=Inspection after the previous patch-context failure showed that the standalone opencode_provider.py file was partially applied before the ambiguous server hunk failed, while its test and all Hub integration were not. Materially adapt by preserving that exact partial file and adding only its fake-process proof in this wave; server integration remains separate. |
| 1787 | 2026-08-14T09:47:34.920Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1788 | 2026-08-14T09:47:35.066Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1789 | 2026-08-14T09:47:35.218Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1790 | 2026-08-14T09:47:35.385Z | state_transition | READY | ROUTED | reason=route_selected |
| 1791 | 2026-08-14T09:47:35.977Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=03c834fb927c48788eea72b0882e0690 |
| 1792 | 2026-08-14T09:47:36.120Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1793 | 2026-08-14T09:47:36.752Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=03c834fb927c48788eea72b0882e0690 |
| 1794 | 2026-08-14T09:47:36.921Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1795 | 2026-08-14T09:47:37.717Z | proof_recorded |  |  | stage_id=check:08da02dda79b9e94; status=passed; cache_hit=False; input_fingerprint=f77ffb62150f509511ed48119a67ff6802af82dc2691ce908a5510ade798d808 |
| 1796 | 2026-08-14T09:47:39.067Z | proof_recorded |  |  | stage_id=check:94a8a740323528c0; status=passed; cache_hit=False; input_fingerprint=52608daf55de58488c361d5ed926b3ba32977087a40f6e01226fad54a23a8798 |
| 1797 | 2026-08-14T09:47:39.526Z | proof_recorded |  |  | stage_id=check:3757086afd1e0527; status=passed; cache_hit=False; input_fingerprint=56e351f66f4836137db7e4f98f2387feb8bee16d10b4fe238b3abedafd9dc821 |
| 1798 | 2026-08-14T09:47:39.855Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1799 | 2026-08-14T09:47:57.071Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:08da02dda79b9e94 | passed | f77ffb62150f509511ed48119a67ff6802af82dc2691ce908a5510ade798d808 | False | 199 | 0 |
| check:94a8a740323528c0 | passed | 52608daf55de58488c361d5ed926b3ba32977087a40f6e01226fad54a23a8798 | False | 1007 | 0 |
| check:3757086afd1e0527 | passed | 56e351f66f4836137db7e4f98f2387feb8bee16d10b4fe238b3abedafd9dc821 | False | 126 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5d539f294f7047699b50b930e76c7063 | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | c56162a6fd442e9db91e362fa2998356c071d62196ca033ffdd01fc879ae8689 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `ee8cc004e9786bf67c9747af4f6e22f058ab2c0fd35aba2e9090d46ad078f03e`
