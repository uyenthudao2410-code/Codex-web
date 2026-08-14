# Orchestration Wave 2

- Run: `ff4a12a96ce549d4871195fc9d77428f`
- Wave: `463fbfdecb91459bab8e2fd18418461e`
- Objective: Complete the remaining non-UI technical roadmap for Tools-Codex-web without changing the Smart-v3 public 8-tool contract. Implement a canonical measured UsageEvent contract/projection with provenance, measured-vs-estimated identity, cached/reasoning token counters, queue/provider/total timing and typed provider error classification; integrate existing OpenCode telemetry into that contract. Implement a Hub-side OpenCode read-only Provider Adapter that can dispatch an explicitly selected allowlisted OpenCode Go model (Flash/Pro) with a bounded prompt packet, timeout/cancel lifecycle, exact run/wave/session/model correlation, usage/cost capture, and fail-closed no-native-write semantics. Implement shadow provider routing as recommendation/evidence only (no automatic mutation or controller transfer), with durable accepted-task route/economics fields sufficient for later cohort calibration. Preserve current controller/write fencing, current routing thresholds, OpenCode worker-only role, existing concurrent UI work, and existing exact telemetry semantics. Do not touch renderer/UI files, do not restart Electron/runtime, do not change permission settings, do not run paid/provider inference solely for proof, and do not commit/push/release/deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `2f496c0edd29d1013afb3daa44ea4300d2bfcb923286768df8d4f4ff9619fe9b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1735 | 2026-08-14T09:38:43.841Z | wave_replanned |  | PREFLIGHT | reason=The prior Sol deep candidate was blocked before mutation with candidate_scope_missing. Materially change strategy by splitting the broad roadmap into deterministic behavior packets; this wave implements only the localized measurement contract using exact known server/ledger integration points, leaving provider dispatch and shadow routing to later accepted waves. |
| 1736 | 2026-08-14T09:38:44.086Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1737 | 2026-08-14T09:38:44.300Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1738 | 2026-08-14T09:38:44.503Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1739 | 2026-08-14T09:38:44.694Z | state_transition | READY | ROUTED | reason=route_selected |
| 1740 | 2026-08-14T09:38:45.335Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ecd1aee0818440ccabbb9e99cba70c2e |
| 1741 | 2026-08-14T09:38:45.517Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1742 | 2026-08-14T09:38:46.418Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ecd1aee0818440ccabbb9e99cba70c2e |
| 1743 | 2026-08-14T09:38:46.583Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1744 | 2026-08-14T09:38:47.615Z | proof_recorded |  |  | stage_id=check:9ec7b67d368443f8; status=passed; cache_hit=False; input_fingerprint=e4358c85a2817587698770c13f0f176f1ee284eb0984b8e2566284186a161096 |
| 1745 | 2026-08-14T09:38:48.316Z | proof_recorded |  |  | stage_id=check:cc2f1f958275bce8; status=failed; cache_hit=False; input_fingerprint=4465cce626bb4fa9547708d506c66a9595a08d09bfb47b8558b7b11fd4b540a0 |
| 1746 | 2026-08-14T09:38:48.486Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 1747 | 2026-08-14T09:38:48.700Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9ec7b67d368443f8 | passed | e4358c85a2817587698770c13f0f176f1ee284eb0984b8e2566284186a161096 | False | 346 | 0 |
| check:cc2f1f958275bce8 | failed | 4465cce626bb4fa9547708d506c66a9595a08d09bfb47b8558b7b11fd4b540a0 | False | 386 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `98be1f371f0f6a3a76beb00d30c943e7e27fef27d4e71efeb254dab6e4fa67ed`
